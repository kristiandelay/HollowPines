#pragma once
#include "Components/ActorComponent.h"
#include "Engine/DataAsset.h"
#include "HollowPinesPlayerGore.generated.h"

class USkeletalMeshComponent;
class UNiagaraSystem;
class ULyraHealthSet;
struct FGameplayEffectSpec;

UCLASS(BlueprintType)
class UHollowPinesGoreProfile : public UDataAsset
{
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere) TSubclassOf<AActor> PainterClass;
    UPROPERTY(EditAnywhere) TObjectPtr<UNiagaraSystem> ImpactEffect;
    UPROPERTY(EditAnywhere) TObjectPtr<UNiagaraSystem> SliceEffect;
    UPROPERTY(EditAnywhere) TObjectPtr<UNiagaraSystem> BleedEffect;
    UPROPERTY(EditAnywhere) TArray<TObjectPtr<UStaticMesh>> OrganMeshes;
    UPROPERTY(EditAnywhere) TObjectPtr<UMaterialInterface> CutMaterial;
    UPROPERTY(EditAnywhere) float BleedSeconds=8;
    UPROPERTY(EditAnywhere) float OrganDropChance=.35f;
};

USTRUCT(BlueprintType)
struct FHPPlayerWound
{
    GENERATED_BODY()
    UPROPERTY(BlueprintReadOnly) int32 Id=0;
    UPROPERTY(BlueprintReadOnly) FName Bone;
    UPROPERTY(BlueprintReadOnly) FVector LocalPoint=FVector::ZeroVector;
    UPROPERTY(BlueprintReadOnly) FVector LocalNormal=FVector::ForwardVector;
    UPROPERTY(BlueprintReadOnly) float Strength=.5f;
    UPROPERTY(BlueprintReadOnly) bool bSlice=false;
    UPROPERTY(BlueprintReadOnly) FName SeverBone;
    UPROPERTY(BlueprintReadOnly) bool bDropOrgans=false;
    UPROPERTY(BlueprintReadOnly) int32 Seed=0;
    UPROPERTY(BlueprintReadOnly) float ServerTime=0;
};

/** Presentation only. Lyra owns health/damage; wounds follow the selected visual. */
UCLASS(BlueprintType,meta=(BlueprintSpawnableComponent))
class UHollowPinesPlayerGore : public UActorComponent
{
    GENERATED_BODY()
public:
    UHollowPinesPlayerGore();
    UPROPERTY(EditDefaultsOnly) TSoftObjectPtr<UHollowPinesGoreProfile> ProfileAsset;
    UPROPERTY(BlueprintReadOnly,ReplicatedUsing=OnRep_Wounds) TArray<FHPPlayerWound> Wounds;
    UPROPERTY(BlueprintReadOnly) int32 RenderedWoundCount=0;
    UPROPERTY(BlueprintReadOnly) int32 SeveredLimbCount=0;
    UPROPERTY(BlueprintReadOnly) int32 DroppedOrganCount=0;
    UFUNCTION(BlueprintCallable,BlueprintAuthorityOnly) void ApplyWound(const FHitResult& Hit,float Damage,bool bSlice,bool bLethal);
    UFUNCTION(BlueprintPure) static bool IsPermittedCutBone(FName Bone);
    virtual void TickComponent(float DeltaTime,ELevelTick TickType,FActorComponentTickFunction* Function) override;
    virtual void EndPlay(EEndPlayReason::Type Reason) override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& Out) const override;
private:
    UFUNCTION() void OnRep_Wounds();
    void OnHealthChanged(AActor* Instigator,AActor* Causer,const FGameplayEffectSpec* Spec,float Magnitude,float Old,float New);
    void RenderWound(const FHPPlayerWound& Wound,USkeletalMeshComponent* Mesh);
    void Paint(USkeletalMeshComponent* Mesh,FVector Location,float Strength,float Radius);
    bool SeverLimb(USkeletalMeshComponent* Mesh,FName Bone,const FHPPlayerWound& Wound);
    USkeletalMeshComponent* VisualMesh() const;
    UPROPERTY(Transient) TObjectPtr<UHollowPinesGoreProfile> Profile;
    UPROPERTY(Transient) TObjectPtr<AActor> Painter;
    TWeakObjectPtr<const ULyraHealthSet> BoundHealth;
    TWeakObjectPtr<USkeletalMeshComponent> PreparedMesh;
    TSet<int32> RenderedIds;
    TSet<FName> SeveredBones;
    TArray<TWeakObjectPtr<UActorComponent>> TemporaryComponents;
    int32 NextId=1;
};
