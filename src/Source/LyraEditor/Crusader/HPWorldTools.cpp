#include "HPWorldTools.h"
#include "Animation/AnimBlueprint.h"
#include "Animation/AnimSequence.h"
#include "Animation/BlendSpace.h"
#include "AnimGraphNode_Root.h"
#include "AnimGraphNode_BlendSpacePlayer.h"
#include "AnimGraphNode_SequenceEvaluator.h"
#include "AnimGraphNode_TwoWayBlend.h"
#include "K2Node_VariableGet.h"
#include "K2Node_VariableSet.h"
#include "K2Node_FunctionEntry.h"
#include "K2Node_CallFunction.h"
#include "K2Node_InputKey.h"
#include "K2Node_CustomEvent.h"
#include "K2Node_Event.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "NavMesh/NavMeshBoundsVolume.h"
#include "NavigationSystem.h"
#include "EngineUtils.h"
#include "Builders/CubeBuilder.h"
#include "Engine/Polys.h"
#include "Model.h"
#include "Components/BrushComponent.h"
#include "UDynamicMesh.h"
#include "DynamicMesh/DynamicMeshAttributeSet.h"
#include "MeshPartition.h"
#include "MeshPartitionDefinition.h"
#include "MeshPartitionComponent.h"
#include "MeshPartitionModifierActor.h"
#include "Modifiers/MeshPartitionMeshProvider.h"

template<class T> static T* AddNode(UEdGraph* Graph,int32 X,int32 Y)
{
    auto* Node=NewObject<T>(Graph);
    Graph->AddNode(Node,true,false);Node->CreateNewGuid();Node->PostPlacedNewNode();Node->AllocateDefaultPins();
    Node->NodePosX=X;Node->NodePosY=Y;return Node;
}
bool UHPWorldTools::BuildCreatureAnimation(UAnimBlueprint* Blueprint,UBlendSpace* Locomotion,UAnimSequence* Fallback)
{
    if (!Blueprint || !Locomotion || !Fallback) return false;
    TArray<UEdGraph*> Graphs;Blueprint->GetAllGraphs(Graphs);
    for (auto* Graph:Graphs)
    {
        if (Graph->GetFName()!=TEXT("AnimGraph")) continue;
        UAnimGraphNode_Root* Root=nullptr;
        const auto Old=Graph->Nodes;
        for (UEdGraphNode* Node:Old)
            if (auto* R=Cast<UAnimGraphNode_Root>(Node)) Root=R;
            else FBlueprintEditorUtils::RemoveNode(Blueprint,Node,true);
        if (!Root) return false;
        Root->BreakAllNodeLinks();
        auto* Move=AddNode<UAnimGraphNode_BlendSpacePlayer>(Graph,-450,-120);
        Move->Node.SetBlendSpace(Locomotion);Move->ReconstructNode();
        auto* Action=AddNode<UAnimGraphNode_SequenceEvaluator>(Graph,-450,150);
        Action->Node.SetSequence(Fallback);Action->Node.SetShouldLoop(false);
        for (auto& Pin:Action->ShowPinForProperties) if (Pin.PropertyName==TEXT("Sequence")) Pin.bShowPin=true;
        Action->ReconstructNode();
        auto* Blend=AddNode<UAnimGraphNode_TwoWayBlend>(Graph,-80,0);
        const auto* Schema=Graph->GetSchema();
        auto Link=[Schema](UEdGraphNode* A,const TCHAR* AP,UEdGraphNode* B,const TCHAR* BP)
        {const auto* Out=A->FindPin(AP); const auto* In=B->FindPin(BP);return Out&&In&&Schema->TryCreateConnection(const_cast<UEdGraphPin*>(Out),const_cast<UEdGraphPin*>(In));};
        auto Var=[Graph,&Link](const TCHAR* Name,UEdGraphNode* Node,const TCHAR* Pin,int32 Y)
        {auto* V=AddNode<UK2Node_VariableGet>(Graph,-750,Y);V->VariableReference.SetSelfMember(Name);V->ReconstructNode();return Link(V,Name,Node,Pin);};
        const bool OK=Var(TEXT("Speed"),Move,TEXT("X"),-100)
            && Var(TEXT("ActionSequence"),Action,TEXT("Sequence"),200)
            && Var(TEXT("ActionTime"),Action,TEXT("ExplicitTime"),320)
            && Var(TEXT("ActionWeight"),Blend,TEXT("Alpha"),440)
            && Link(Move,TEXT("Pose"),Blend,TEXT("A"))
            && Link(Action,TEXT("Pose"),Blend,TEXT("B"))
            && Link(Blend,TEXT("Pose"),Root,TEXT("Result"));
        FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint);
        FKismetEditorUtilities::CompileBlueprint(Blueprint);
        return OK && Blueprint->Status!=BS_Error;
    }
    return false;
}
bool UHPWorldTools::ConfigureLocomotion(UBlendSpace* BlendSpace,UAnimSequence* Idle,UAnimSequence* Walk,UAnimSequence* Run,float WalkSpeed,float RunSpeed)
{
    if (!BlendSpace || !Idle || !Walk || !Run) return false;
    BlendSpace->SetSkeleton(Idle->GetSkeleton());
    // Blend parameters are reflected editor data, so set the axis before adding samples.
    auto* Property=FindFProperty<FStructProperty>(UBlendSpace::StaticClass(),TEXT("BlendParameters"));
    if (!Property) return false;
    auto* Axis=Property->ContainerPtrToValuePtr<FBlendParameter>(BlendSpace,0);
    Axis->DisplayName=TEXT("Speed");Axis->Min=0;Axis->Max=RunSpeed;Axis->GridNum=8;
    while (BlendSpace->GetNumberOfBlendSamples()) BlendSpace->DeleteSample(BlendSpace->GetNumberOfBlendSamples()-1);
    const int32 A=BlendSpace->AddSample(Idle,FVector::ZeroVector);
    const int32 B=BlendSpace->AddSample(Walk,FVector(WalkSpeed,0,0));
    const int32 C=BlendSpace->AddSample(Run,FVector(RunSpeed,0,0));
    BlendSpace->ValidateSampleData();BlendSpace->ResampleData();BlendSpace->PostEditChange();BlendSpace->MarkPackageDirty();
    return A>=0&&B>=0&&C>=0;
}
ANavMeshBoundsVolume* UHPWorldTools::AddNavigationBounds(UWorld* World,FVector Center,FVector Size)
{
    if (!World) return nullptr;
    auto* Volume=World->SpawnActor<ANavMeshBoundsVolume>(Center,FRotator::ZeroRotator);
    Volume->Brush=NewObject<UModel>(Volume,NAME_None,RF_Transactional);
    Volume->Brush->Initialize(nullptr,true);
    Volume->Brush->Polys=NewObject<UPolys>(Volume->Brush,NAME_None,RF_Transactional);
    Volume->GetBrushComponent()->Brush=Volume->Brush;
    auto* Builder=NewObject<UCubeBuilder>(Volume);
    Volume->BrushBuilder=Builder;
    Builder->X=Size.X;Builder->Y=Size.Y;Builder->Z=Size.Z;
    Builder->Build(World,Volume);
    Volume->GetBrushComponent()->BuildSimpleBrushCollision();
    Volume->PostEditChange();
    if (auto* Nav=FNavigationSystem::GetCurrent<UNavigationSystemV1>(World)) Nav->OnNavigationBoundsUpdated(Volume);
    return Volume;
}

FString UHPWorldTools::BuildNavigation(UWorld* World)
{
    auto* Nav=FNavigationSystem::GetCurrent<UNavigationSystemV1>(World);
    if (!Nav) return TEXT("No navigation system");
    for (TActorIterator<ANavMeshBoundsVolume> It(World);It;++It) Nav->OnNavigationBoundsUpdated(*It);
    Nav->Build();
    const auto* Data=Nav->GetDefaultNavDataInstance(FNavigationSystem::DontCreate);
    return FString::Printf(TEXT("Data=%s Bounds=%s"),*GetNameSafe(Data),*Nav->GetNavigableWorldBounds().ToString());
}

AActor* UHPWorldTools::CreateMeshTerrain(UWorld* World,UObject* Definition)
{
    using namespace UE::MeshPartition;
    if (!World || !Cast<UMeshPartitionDefinition>(Definition)) return nullptr;
    auto* Terrain=World->SpawnActor<AMeshPartition>();
    Terrain->SetMeshPartitionDefinition(Cast<UMeshPartitionDefinition>(Definition));
    UClass* EditorClass=LoadClass<UMeshPartitionComponent>(nullptr,TEXT("/Script/MeshPartitionEditor.MeshPartitionEditorComponent"));
    if (EditorClass && (!Terrain->GetMeshPartitionComponent() || !Terrain->GetMeshPartitionComponent()->IsA(EditorClass)))
    {
        auto* EditorComponent=NewObject<UMeshPartitionComponent>(Terrain,EditorClass,NAME_None,RF_Transactional);
        Terrain->AddInstanceComponent(EditorComponent);
        Terrain->SetMeshPartitionComponent(EditorComponent);
        EditorComponent->RegisterComponent();
    }
    Terrain->SetActorLabel(TEXT("Blackwater Mesh Terrain"));
    Terrain->PostEditChange();
    return Terrain;
}
AActor* UHPWorldTools::AddMeshTerrainSection(AActor* TerrainActor,UDynamicMesh* Mesh,const FString& Label)
{
    using namespace UE::MeshPartition;
    auto* Terrain=Cast<AMeshPartition>(TerrainActor);
    if (!Terrain || !Mesh) return nullptr;
    auto* Actor=Terrain->GetWorld()->SpawnActor<AModifierActor>();
    Actor->SetActorLabel(Label);
    auto* Provider=NewObject<UMeshProviderModifier>(Actor,NAME_None,RF_Transactional);
    Actor->AddInstanceComponent(Provider);Actor->Modifier=Provider;
    Provider->SetupAttachment(Actor->GetRootComponent());
    Provider->SetAffectedMeshPartition(Terrain);
    Mesh->ProcessMesh([Provider](const UE::Geometry::FDynamicMesh3& Source){ Provider->SetMesh(UE::Geometry::FDynamicMesh3(Source)); });
    Provider->RegisterComponent();
    Provider->BP_SetAffectedMegaMesh(Terrain);
    Actor->PostEditChange();
    return Actor;
}

UDynamicMesh* UHPWorldTools::GetMeshTerrainSection(AActor* Section)
{
    using namespace UE::MeshPartition;
    auto* Provider=Section ? Section->FindComponentByClass<UMeshProviderModifier>() : nullptr;
    if (!Provider || !Provider->GetMesh()) return nullptr;
    auto* Result=NewObject<UDynamicMesh>();
    Result->SetMesh(UE::Geometry::FDynamicMesh3(*Provider->GetMesh()));
    return Result;
}

FString UHPWorldTools::CleanMeshTerrainWeights(AActor* Section)
{
    auto* Provider=Section?Section->FindComponentByClass<UE::MeshPartition::UMeshProviderModifier>():nullptr;
    if (!Provider || !Provider->GetMesh()) return TEXT("No provider mesh");
    UE::Geometry::FDynamicMesh3 Mesh(*Provider->GetMesh());FString Names;
    if (Mesh.HasAttributes())
    {
        for(int32 I=0;I<Mesh.Attributes()->NumWeightLayers();++I) Names+=Mesh.Attributes()->GetWeightLayer(I)->GetName().ToString()+TEXT(" ");
        Mesh.Attributes()->SetNumWeightLayers(0);
    }
    Provider->SetMesh(MoveTemp(Mesh));Provider->MarkPackageDirty();Section->MarkPackageDirty();
    return Names;
}

bool UHPWorldTools::ConfigureGorePainter(UBlueprint* Blueprint)
{
    if (!Blueprint) return false;
    bool bRoutedMesh=false;
    TArray<UEdGraph*> Graphs;Blueprint->GetAllGraphs(Graphs);
    for (auto* Graph:Graphs)
    {
        const auto Nodes=Graph->Nodes;
        for (UEdGraphNode* Node:Nodes)
        {
            // This copy is a receiver driven by authoritative Lyra damage. The
            // vendor's demo mouse input and continuous firing are not applicable.
            if (Cast<UK2Node_InputKey>(Node)) FBlueprintEditorUtils::RemoveNode(Blueprint,Node,true);
            if (auto* Event=Cast<UK2Node_Event>(Node);Event && Event->EventReference.GetMemberName()==TEXT("ReceiveTick"))
                if (auto* Pin=Event->FindPin(TEXT("then"))) Pin->BreakAllPinLinks();
            // The demo also loops through a latent custom event to follow the
            // first local pawn. That pawn can be absent during respawn; this
            // receiver positions its isolated capture explicitly when painting.
            if (auto* Event=Cast<UK2Node_CustomEvent>(Node);Event && Event->CustomFunctionName.ToString().Replace(TEXT(" "),TEXT(""))==TEXT("DelayedTick"))
                if (auto* Pin=Event->FindPin(TEXT("then"))) Pin->BreakAllPinLinks();
            if (auto* Call=Cast<UK2Node_CallFunction>(Node);Call && Call->FunctionReference.GetMemberName()==TEXT("EnableInput"))
            {
                auto* In=Call->FindPin(TEXT("execute"));auto* Out=Call->FindPin(TEXT("then"));
                if (In && Out)
                {
                    const auto Before=In->LinkedTo;const auto After=Out->LinkedTo;
                    In->BreakAllPinLinks();Out->BreakAllPinLinks();
                    for(auto* A:Before) for(auto* B:After) Graph->GetSchema()->TryCreateConnection(A,B);
                }
            }
        }
        if (Graph->GetFName()==TEXT("PaintActor"))
        {
            for(UEdGraphNode* Node:Nodes)
                if(auto* Call=Cast<UK2Node_CallFunction>(Node);Call && Call->FunctionReference.GetMemberName()==TEXT("CreateRenderTarget2D"))
                    for(const FName Size:{FName(TEXT("Width")),FName(TEXT("Height"))})
                        if(auto* Pin=Call->FindPin(Size)) Graph->GetSchema()->TrySetDefaultValue(*Pin,TEXT("1024"));
            // The project supplies its selected mesh explicitly. These demo
            // branches otherwise dereference an optional InsidesPlacer component
            // just to decide whether this is a MetaHuman or a named child mesh.
            for(UEdGraphNode* Node:Nodes)
                if(auto* Get=Cast<UK2Node_VariableGet>(Node))
                {
                    const FName Name=Get->VariableReference.GetMemberName();
                    if(Name==TEXT("IsMetaHuman") || Name==TEXT("Use SkeletalMesh by name"))
                        if(auto* Pin=Get->FindPin(Name))
                        {
                            const auto Targets=Pin->LinkedTo;Pin->BreakAllPinLinks();
                            for(auto* Target:Targets) Graph->GetSchema()->TrySetDefaultValue(*Target,TEXT("false"));
                        }
                }
            UEdGraphPin* MeshPin=nullptr;
            for (UEdGraphNode* Node:Nodes) if (auto* Entry=Cast<UK2Node_FunctionEntry>(Node)) MeshPin=Entry->FindPin(TEXT("SkeleMeshComp"));
            if (!MeshPin) return false;
            for (UEdGraphNode* Node:Nodes)
                if (auto* Set=Cast<UK2Node_VariableSet>(Node);Set && Set->VariableReference.GetMemberName()==TEXT("Mesh"))
                    if (auto* Pin=Set->FindPin(TEXT("Mesh")))
                    {Pin->BreakAllPinLinks();bRoutedMesh|=Graph->GetSchema()->TryCreateConnection(MeshPin,Pin);}
        }
    }
    FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint);
    FKismetEditorUtilities::CompileBlueprint(Blueprint);
    return bRoutedMesh && Blueprint->Status!=BS_Error;
}
