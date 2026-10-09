#include "HollowPinesPlayerGore.h"
#include "AbilitySystemGlobals.h"
#include "AbilitySystemComponent.h"
#include "AbilitySystem/Attributes/LyraHealthSet.h"
#include "Baseline/BaselineEquipment.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/SphereComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SceneCaptureComponent2D.h"
#include "Engine/SkeletalMesh.h"
#include "GameFramework/GameStateBase.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "NativeGameplayTags.h"
#include "Net/UnrealNetwork.h"
#include "NiagaraFunctionLibrary.h"
#include "NiagaraComponent.h"
#include "ProceduralMeshComponent.h"
#include "KismetProceduralMeshLibrary.h"
#include "Kismet/KismetRenderingLibrary.h"
#include "Rendering/SkeletalMeshRenderData.h"
#include "Rendering/SkeletalMeshLODRenderData.h"
#include "Rendering/SkinWeightVertexBuffer.h"
#include "UObject/StructOnScope.h"
#include "TimerManager.h"

UE_DEFINE_GAMEPLAY_TAG_STATIC(TAG_HP_Slash,"HollowPines.Damage.Slash");

static float GoreTime(const UWorld* World)
{
    const auto* GS=World->GetGameState();return GS?GS->GetServerWorldTimeSeconds():World->GetTimeSeconds();
}
// Custom survivor clothing sits at different distances from the shared UE bones
// and hit bodies. Keep the brush on the currently skinned visible surface.
static FVector GoreSurfacePoint(USkeletalMeshComponent* Mesh,const FVector& WorldPoint)
{
    const auto* Asset=Mesh->GetSkeletalMeshAsset();
    const auto* Data=Asset?Asset->GetResourceForRendering():nullptr;
    if (!Data || Data->LODRenderData.IsEmpty()) return WorldPoint;
    const int32 LOD=FMath::Min(2,Data->LODRenderData.Num()-1);
    const auto& Render=Data->LODRenderData[LOD];
    const auto* Weights=Mesh->GetSkinWeightBuffer(LOD);
    if (!Weights || !Weights->GetNeedsCPUAccess()) return WorldPoint;
    TArray<FMatrix44f> Matrices;Mesh->GetCurrentRefToLocalMatrices(Matrices,LOD);
    const FTransform& Transform=Mesh->GetComponentTransform();
    const FVector LocalPoint=Transform.InverseTransformPosition(WorldPoint);
    float ClosestDistance=FMath::Square(40.f);FVector Closest=LocalPoint;
    for (uint32 V=0;V<Render.GetNumVertices();++V)
    {
        const FVector Position(USkeletalMeshComponent::GetSkinnedVertexPosition(Mesh,V,Render,*Weights,Matrices));
        const float Distance=FVector::DistSquared(Position,LocalPoint);
        if (Distance<ClosestDistance) {ClosestDistance=Distance;Closest=Position;}
    }
    return Transform.TransformPosition(Closest);
}
static AActor* GoreDebris(UWorld* World,FVector Location,float Radius)
{
    FActorSpawnParameters Params;Params.ObjectFlags|=RF_Transient;
    auto* Actor=World->SpawnActor<AActor>(Params);
    auto* Body=NewObject<USphereComponent>(Actor);
    Actor->AddInstanceComponent(Body);Actor->SetRootComponent(Body);
    Body->InitSphereRadius(Radius);Body->SetCollisionProfileName(TEXT("PhysicsActor"));
    Body->SetCollisionResponseToChannel(ECC_Pawn,ECR_Ignore);
    Body->SetCollisionResponseToChannel(ECC_Camera,ECR_Ignore);
    Body->SetCanEverAffectNavigation(false);Body->RegisterComponent();
    Actor->SetActorLocation(Location);Actor->SetLifeSpan(30);
    Actor->Tags.Add(TEXT("HollowPinesGoreDebris"));
    return Actor;
}

UHollowPinesPlayerGore::UHollowPinesPlayerGore()
{
    SetIsReplicatedByDefault(true);
    PrimaryComponentTick.bCanEverTick=true;PrimaryComponentTick.TickInterval=.05f;
    // Capture after skeletal animation and visual-retarget transforms finish.
    // Capturing during PrePhysics can render an empty first wound mask.
    PrimaryComponentTick.TickGroup=TG_PostUpdateWork;
    ProfileAsset=TSoftObjectPtr<UHollowPinesGoreProfile>(FSoftObjectPath(TEXT("/Game/HollowPines/Gore/DA_PlayerGore.DA_PlayerGore")));
}
void UHollowPinesPlayerGore::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);DOREPLIFETIME(UHollowPinesPlayerGore,Wounds);
}
USkeletalMeshComponent* UHollowPinesPlayerGore::VisualMesh() const
{
    const auto* Equipment=GetOwner()->FindComponentByClass<UBaselineEquipmentComponent>();
    return Equipment?Equipment->GetPresentationMesh():GetOwner()->FindComponentByClass<USkeletalMeshComponent>();
}
bool UHollowPinesPlayerGore::IsPermittedCutBone(FName Bone)
{
    // An allowlist deliberately excludes every spine/root/pelvis/torso bone.
    static const TSet<FName> Allowed={TEXT("head"),TEXT("upperarm_l"),TEXT("upperarm_r"),TEXT("lowerarm_l"),TEXT("lowerarm_r"),TEXT("thigh_l"),TEXT("thigh_r"),TEXT("calf_l"),TEXT("calf_r")};
    return Allowed.Contains(Bone);
}
void UHollowPinesPlayerGore::ApplyWound(const FHitResult& Hit,float Damage,bool bSlice,bool bLethal)
{
    if (!GetOwner()->HasAuthority() || Damage<=0) return;
    auto* Mesh=VisualMesh();if (!Mesh || !Mesh->GetSkeletalMeshAsset()) return;
    FVector Point=Hit.ImpactPoint;
    if (Point.IsNearlyZero() || FVector::DistSquared(Point,Mesh->GetComponentLocation())>FMath::Square(350.f)) Point=Mesh->GetSocketLocation(TEXT("spine_03"));
    FName Bone=Hit.BoneName;
    if (Mesh->GetBoneIndex(Bone)==INDEX_NONE || Bone==TEXT("root")) Bone=Mesh->FindClosestBone(Point);
    const FTransform Frame=Mesh->GetSocketTransform(Bone);
    FHPPlayerWound Wound;
    Wound.Id=NextId++;Wound.Bone=Bone;Wound.LocalPoint=Frame.InverseTransformPosition(Point);
    Wound.LocalNormal=Frame.InverseTransformVectorNoScale(Hit.ImpactNormal.IsNearlyZero()?GetOwner()->GetActorForwardVector():FVector(Hit.ImpactNormal));
    Wound.Strength=FMath::Clamp(Damage/70.f,.25f,.9f);Wound.bSlice=bSlice;
    Wound.Seed=FMath::Rand();Wound.ServerTime=GoreTime(GetWorld());
    // Nonfatal slices leave wounds. Fatal slices may sever one limb while the
    // existing death/ragdoll lifecycle remains responsible for the player.
    if (bSlice && bLethal)
    {
        FName Candidate=Bone;
        while (!Candidate.IsNone())
        {
            if (IsPermittedCutBone(Candidate)) {Wound.SeverBone=Candidate;break;}
            Candidate=Mesh->GetParentBone(Candidate);
        }
    }
    const FString BoneText=Bone.ToString();
    Wound.bDropOrgans=(bLethal || (bSlice && Damage>=35)) && (BoneText.StartsWith(TEXT("spine")) || Bone==TEXT("pelvis"));
    if (Wounds.Num()>=16) Wounds.RemoveAt(0);
    Wounds.Add(Wound);GetOwner()->ForceNetUpdate();OnRep_Wounds();
}
void UHollowPinesPlayerGore::OnHealthChanged(AActor*,AActor*,const FGameplayEffectSpec* Spec,float,float Old,float New)
{
    if (!GetOwner()->HasAuthority() || New>=Old || !Spec) return;
    const FHitResult* Hit=Spec->GetContext().GetHitResult();
    if (!Hit) return; // Falls/environmental health changes do not invent impact wounds.
    FGameplayTagContainer Tags;Spec->GetAllAssetTags(Tags);
    ApplyWound(*Hit,Old-New,Tags.HasTag(TAG_HP_Slash),New<=0);
}
void UHollowPinesPlayerGore::OnRep_Wounds() {SetComponentTickEnabled(true);}
void UHollowPinesPlayerGore::TickComponent(float DeltaTime,ELevelTick TickType,FActorComponentTickFunction* Function)
{
    Super::TickComponent(DeltaTime,TickType,Function);
    if (GetOwner()->HasAuthority() && !BoundHealth.IsValid())
        if (auto* ASC=UAbilitySystemGlobals::GetAbilitySystemComponentFromActor(GetOwner()))
            if (const auto* Health=ASC->GetSet<ULyraHealthSet>())
            {BoundHealth=Health;Health->OnHealthChanged.AddUObject(this,&ThisClass::OnHealthChanged);}
    if (GetNetMode()==NM_DedicatedServer || Wounds.IsEmpty()) return;
    auto* Mesh=VisualMesh();if (!Mesh || !Mesh->GetSkeletalMeshAsset() || !Mesh->GetAnimInstance()) return;
    if (PreparedMesh.Get()!=Mesh)
    {
        if (Painter) Painter->Destroy();Painter=nullptr;
        PreparedMesh=Mesh;RenderedIds.Reset();SeveredBones.Reset();RenderedWoundCount=0;
    }
    if (!Profile) Profile=ProfileAsset.LoadSynchronous();
    if (!Profile || !Profile->PainterClass) return;
    if (!Painter)
    {
        FActorSpawnParameters Params;Params.Owner=GetOwner();Params.ObjectFlags|=RF_Transient;
        Painter=GetWorld()->SpawnActor<AActor>(Profile->PainterClass,Params);
        if (Painter)
        {
            Painter->SetReplicates(false);Painter->SetActorTickEnabled(false);
            auto* Capture=Painter->FindComponentByClass<USceneCaptureComponent2D>();
            if(Capture)
            {
                Capture->PrimitiveRenderMode=ESceneCapturePrimitiveRenderMode::PRM_UseShowOnlyList;
                Capture->ClearShowOnlyComponents();Capture->ShowOnlyComponent(Mesh);
            }
            // The package's first PaintActor call allocates per-character render
            // targets/materials. Prime it without paint, then draw next frame.
            Paint(Mesh,Mesh->GetComponentLocation(),0,1);
            // Warm the capture/material path as well as allocation. UE creates
            // the unwrap scene proxy on its first capture; that frame is blank.
            Paint(Mesh,Mesh->GetComponentLocation(),0,1);
            if(Capture && Capture->TextureTarget)
                UKismetRenderingLibrary::ClearRenderTarget2D(GetWorld(),Capture->TextureTarget,FLinearColor::Black);
        }
        return; // Allow its render-target initialization to finish for a frame.
    }
    for (const auto& Wound:Wounds)
        if (!RenderedIds.Contains(Wound.Id))
        {RenderWound(Wound,Mesh);RenderedIds.Add(Wound.Id);++RenderedWoundCount;break;}
}
void UHollowPinesPlayerGore::Paint(USkeletalMeshComponent* Mesh,FVector Location,float Strength,float Radius)
{
    auto* Function=Painter?Painter->FindFunction(TEXT("PaintActor")):nullptr;if (!Function) return;
    FStructOnScope Parameters(Function);
    for (TFieldIterator<FProperty> It(Function);It && It->HasAnyPropertyFlags(CPF_Parm);++It)
    {
        void* Value=It->ContainerPtrToValuePtr<void>(Parameters.GetStructMemory());
        const FName Name=It->GetFName();
        if (auto* Object=CastField<FObjectPropertyBase>(*It))
        {
            if (Name==TEXT("ActorToPaint")) Object->SetObjectPropertyValue(Value,GetOwner());
            else if (Name==TEXT("SkeleMeshComp")) Object->SetObjectPropertyValue(Value,Mesh);
        }
        else if (Name==TEXT("HitLocation")) *static_cast<FVector*>(Value)=Location;
        else if (auto* Number=CastField<FNumericProperty>(*It))
        {
            if (Name==TEXT("HitStrength")) Number->SetFloatingPointPropertyValue(Value,Strength);
            else if (Name==TEXT("BrushRadius")) Number->SetFloatingPointPropertyValue(Value,Radius);
        }
    }
    Painter->ProcessEvent(Function,Parameters.GetStructMemory());
}
void UHollowPinesPlayerGore::RenderWound(const FHPPlayerWound& Wound,USkeletalMeshComponent* Mesh)
{
    const FTransform Frame=Mesh->GetSocketTransform(Wound.Bone);
    const FVector Point=GoreSurfacePoint(Mesh,Frame.TransformPosition(Wound.LocalPoint));
    const FVector Normal=Frame.TransformVectorNoScale(Wound.LocalNormal).GetSafeNormal();
    if (Wound.bSlice)
    {
        FVector Along=FVector::CrossProduct(Normal,GetOwner()->GetActorUpVector()).GetSafeNormal();
        if (Along.IsNearlyZero()) Along=GetOwner()->GetActorRightVector();
        for (int32 I=-2;I<=2;++I) Paint(Mesh,Point+Along*I*2.5f,Wound.Strength,3.5f);
    }
    else Paint(Mesh,Point,Wound.Strength,5.5f);
    const float Age=GoreTime(GetWorld())-Wound.ServerTime;
    if (Age<2)
        UNiagaraFunctionLibrary::SpawnSystemAtLocation(GetWorld(),Wound.bSlice?Profile->SliceEffect:Profile->ImpactEffect,Point,Normal.Rotation());
    if (Age<Profile->BleedSeconds && Profile->BleedEffect)
    {
        auto* Bleed=UNiagaraFunctionLibrary::SpawnSystemAttached(Profile->BleedEffect,Mesh,Wound.Bone,Point,Normal.Rotation(),EAttachLocation::KeepWorldPosition,false);
        if (Bleed)
        {
            TemporaryComponents.Add(Bleed);
            FTimerHandle Handle;TWeakObjectPtr<UNiagaraComponent> Weak=Bleed;
            GetWorld()->GetTimerManager().SetTimer(Handle,[Weak](){if (Weak.IsValid()) Weak->DestroyComponent();},FMath::Max(.1f,Profile->BleedSeconds-Age),false);
        }
    }
    if (IsPermittedCutBone(Wound.SeverBone) && !SeveredBones.Contains(Wound.SeverBone))
        if (SeverLimb(Mesh,Wound.SeverBone,Wound)) {SeveredBones.Add(Wound.SeverBone);++SeveredLimbCount;}
    FRandomStream Random(Wound.Seed);
    if (Wound.bDropOrgans && Age<3 && Profile->OrganMeshes.Num() && Random.FRand()<Profile->OrganDropChance)
        for (int32 I=0,Count=Random.RandRange(1,2);I<Count;++I)
        {
            auto* Organ=GoreDebris(GetWorld(),Point+Normal*15+FVector(0,0,10),5);
            auto* Visual=NewObject<UStaticMeshComponent>(Organ);Organ->AddInstanceComponent(Visual);
            Visual->SetupAttachment(Organ->GetRootComponent());Visual->SetStaticMesh(Profile->OrganMeshes[Random.RandRange(0,Profile->OrganMeshes.Num()-1)]);
            Visual->SetCollisionEnabled(ECollisionEnabled::NoCollision);Visual->SetCanEverAffectNavigation(false);Visual->RegisterComponent();
            auto* Body=CastChecked<USphereComponent>(Organ->GetRootComponent());
            Body->SetSimulatePhysics(true);Body->SetPhysicsLinearVelocity(Normal*120+FVector(Random.FRandRange(-70,70),Random.FRandRange(-70,70),100));
            ++DroppedOrganCount;
        }
}

bool UHollowPinesPlayerGore::SeverLimb(USkeletalMeshComponent* Mesh,FName Bone,const FHPPlayerWound& Wound)
{
    if (!IsPermittedCutBone(Bone)) return false;
    auto* Asset=Mesh->GetSkeletalMeshAsset();const auto* Data=Asset?Asset->GetResourceForRendering():nullptr;
    if (!Data || Data->LODRenderData.IsEmpty()) return false;
    const int32 LOD=FMath::Min(2,Data->LODRenderData.Num()-1);
    const auto& Render=Data->LODRenderData[LOD];const auto* Weights=Mesh->GetSkinWeightBuffer(LOD);
    if (!Weights || !Weights->GetNeedsCPUAccess()) return false;
    const auto& Skeleton=Asset->GetRefSkeleton();const int32 Root=Mesh->GetBoneIndex(Bone);
    if (Root==INDEX_NONE) return false;
    TArray<FMatrix44f> Matrices;Mesh->GetCurrentRefToLocalMatrices(Matrices,LOD);
    TArray<bool> Selected;Selected.Init(false,Render.GetNumVertices());
    for (const auto& Section:Render.RenderSections)
        for (uint32 V=Section.BaseVertexIndex;V<Section.BaseVertexIndex+Section.NumVertices;++V)
        {
            uint32 Inside=0,Total=0;
            for (uint32 I=0;I<Weights->GetMaxBoneInfluences();++I)
            {
                const uint32 Weight=Weights->GetBoneWeight(V,I);Total+=Weight;
                const uint32 Local=Weights->GetBoneIndex(V,I);
                if (Section.BoneMap.IsValidIndex(Local))
                {
                    const int32 B=Section.BoneMap[Local];
                    if (B==Root || Skeleton.BoneIsChildOf(B,Root)) Inside+=Weight;
                }
            }
            Selected[V]=Total>0 && Inside*2>=Total;
        }
    const auto* Indices=Render.MultiSizeIndexContainer.GetIndexBuffer();if (!Indices) return false;
    TMap<int32,int32> Remap;TArray<FVector> Vertices;TArray<FVector2D> UVs;TArray<int32> Triangles;
    const FTransform CutFrame=Mesh->GetSocketTransform(Bone);
    auto Vertex=[&](int32 Old)
    {
        if (const auto* Found=Remap.Find(Old)) return *Found;
        const FVector Local(USkeletalMeshComponent::GetSkinnedVertexPosition(Mesh,Old,Render,*Weights,Matrices));
        const int32 New=Vertices.Add(CutFrame.InverseTransformPosition(Mesh->GetComponentTransform().TransformPosition(Local)));
        UVs.Add(FVector2D(Render.StaticVertexBuffers.StaticMeshVertexBuffer.GetVertexUV(Old,0)));
        Remap.Add(Old,New);return New;
    };
    for (int32 I=0;I<Indices->Num();I+=3)
    {
        const int32 A=Indices->Get(I),B=Indices->Get(I+1),C=Indices->Get(I+2);
        if (Selected[A] && Selected[B] && Selected[C]) {Triangles.Add(Vertex(A));Triangles.Add(Vertex(B));Triangles.Add(Vertex(C));}
    }
    if (Triangles.Num()<12) return false;
    TArray<FVector> Normals;TArray<FProcMeshTangent> Tangents;
    UKismetProceduralMeshLibrary::CalculateTangentsForMesh(Vertices,Triangles,UVs,Normals,Tangents);
    AActor* Chunk=GoreDebris(GetWorld(),CutFrame.GetLocation(),12);Chunk->SetActorRotation(CutFrame.Rotator());
    auto* Proc=NewObject<UProceduralMeshComponent>(Chunk);Chunk->AddInstanceComponent(Proc);Proc->SetupAttachment(Chunk->GetRootComponent());
    Proc->SetCollisionEnabled(ECollisionEnabled::NoCollision);Proc->SetCanEverAffectNavigation(false);Proc->RegisterComponent();
    Proc->CreateMeshSection_LinearColor(0,Vertices,Triangles,Normals,UVs,TArray<FLinearColor>(),Tangents,false);
    Proc->SetMaterial(0,Mesh->GetMaterial(0));
    // A blood cap spans the joint opening. It uses a separate material slot and
    // a matching attached stump cap, keeping the protected torso mesh intact.
    // Weld coincident render vertices before finding open boundary loops. UV
    // seams otherwise look like cuts and produce overlapping fans on the skin.
    TMap<FIntVector,int32> Welded;TArray<FVector> Positions;TArray<int32> WeldMap;
    for (const FVector& P:Vertices)
    {
        const FIntVector Key(FMath::RoundToInt(P.X*100),FMath::RoundToInt(P.Y*100),FMath::RoundToInt(P.Z*100));
        const int32* Existing=Welded.Find(Key);
        if(Existing) WeldMap.Add(*Existing);
        else {const int32 Index=Positions.Add(P);Welded.Add(Key,Index);WeldMap.Add(Index);}
    }
    TMap<uint64,int32> EdgeCounts;
    auto EdgeKey=[](int32 A,int32 B){return (uint64(FMath::Min(A,B))<<32)|uint32(FMath::Max(A,B));};
    for(int32 I=0;I<Triangles.Num();I+=3)
        for(int32 J=0;J<3;++J)
        {
            const int32 A=WeldMap[Triangles[I+J]],B=WeldMap[Triangles[I+(J+1)%3]];
            if(A!=B) ++EdgeCounts.FindOrAdd(EdgeKey(A,B));
        }
    TMap<int32,TArray<int32>> Boundary;
    for(const auto& Edge:EdgeCounts) if(Edge.Value==1)
    {
        const int32 A=int32(Edge.Key>>32),B=int32(uint32(Edge.Key));
        Boundary.FindOrAdd(A).Add(B);Boundary.FindOrAdd(B).Add(A);
    }
    TSet<int32> Visited;int32 CapSection=1;
    for(const auto& Start:Boundary)
    {
        if(Visited.Contains(Start.Key) || Start.Value.Num()!=2) continue;
        TArray<FVector> Ring;int32 Previous=INDEX_NONE,Current=Start.Key;
        bool bClosed=false;
        for(int32 Step=0;Step<=Boundary.Num();++Step)
        {
            if(Current==Start.Key && Step>0) {bClosed=true;break;}
            if(Visited.Contains(Current)) break;
            Visited.Add(Current);Ring.Add(Positions[Current]);
            const auto* Next=Boundary.Find(Current);if(!Next || Next->Num()!=2) break;
            const int32 Candidate=(*Next)[0]==Previous?(*Next)[1]:(*Next)[0];
            Previous=Current;Current=Candidate;
        }
        if(!bClosed || Ring.Num()<3) continue;
        FVector Center=FVector::ZeroVector;for(const auto& P:Ring) Center+=P;Center/=Ring.Num();
        if(Center.Size()>28) continue; // Ignore existing garment openings far from the severed joint.
        FVector Axis=FVector::ZeroVector;
        for(int32 I=0;I<Ring.Num();++I) Axis+=FVector::CrossProduct(Ring[I]-Center,Ring[(I+1)%Ring.Num()]-Center);
        Axis.Normalize();FVector U,V;Axis.FindBestAxisVectors(U,V);
        TArray<FVector> Cap={Center};Cap.Append(Ring);TArray<int32> CapIndices;TArray<FVector2D> CapUV;
        for(const auto& P:Cap) CapUV.Add(FVector2D(FVector::DotProduct(P-Center,U),FVector::DotProduct(P-Center,V))/20+FVector2D(.5,.5));
        for(int32 I=1;I<Cap.Num();++I) {CapIndices.Add(0);CapIndices.Add(I);CapIndices.Add(I==Cap.Num()-1?1:I+1);}
        Proc->CreateMeshSection_LinearColor(CapSection,Cap,CapIndices,TArray<FVector>(),CapUV,TArray<FLinearColor>(),TArray<FProcMeshTangent>(),false);
        Proc->SetMaterial(CapSection++,Profile->CutMaterial);
        auto* Stump=NewObject<UProceduralMeshComponent>(GetOwner());GetOwner()->AddInstanceComponent(Stump);
        const FName Parent=Mesh->GetParentBone(Bone);const FTransform ParentFrame=Mesh->GetSocketTransform(Parent);
        for(auto& P:Cap) P=ParentFrame.InverseTransformPosition(CutFrame.TransformPosition(P));
        Stump->SetupAttachment(Mesh,Parent);Stump->SetCollisionEnabled(ECollisionEnabled::NoCollision);Stump->SetCanEverAffectNavigation(false);Stump->RegisterComponent();
        Stump->CreateMeshSection_LinearColor(0,Cap,CapIndices,TArray<FVector>(),CapUV,TArray<FLinearColor>(),TArray<FProcMeshTangent>(),false);
        Stump->SetMaterial(0,Profile->CutMaterial);TemporaryComponents.Add(Stump);
    }
    Mesh->HideBoneByName(Bone,EPhysBodyOp::PBO_None);
    auto* Body=CastChecked<USphereComponent>(Chunk->GetRootComponent());Body->SetSimulatePhysics(true);
    Body->SetPhysicsLinearVelocity(GetOwner()->GetActorForwardVector()*70+FVector(0,0,70));
    return true;
}
void UHollowPinesPlayerGore::EndPlay(EEndPlayReason::Type Reason)
{
    if (BoundHealth.IsValid()) BoundHealth->OnHealthChanged.RemoveAll(this);
    if (Painter) Painter->Destroy();
    for (const auto& Component:TemporaryComponents) if (Component.IsValid()) Component->DestroyComponent();
    Super::EndPlay(Reason);
}
