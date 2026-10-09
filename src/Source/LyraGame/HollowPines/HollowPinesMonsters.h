#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "AIController.h"
#include "Animation/AnimInstance.h"
#include "AbilitySystemInterface.h"
#include "Teams/LyraTeamAgentInterface.h"
#include "Subsystems/WorldSubsystem.h"
#include "Baseline/BaselineEquipment.h"
#include "Engine/DataAsset.h"
#include "Crusader/CRTraversalCharacter.h"
#include "HollowPinesMonsters.generated.h"

class ULyraAbilitySystemComponent;
class ULyraHealthSet;
class ULyraHealthComponent;
class UBlendSpace;
class AHollowPinesMonster;

UENUM(BlueprintType)
enum class EHPMonsterAction : uint8
{
    None, JumpStart, JumpLoop, Land, Attack1, Attack2, Attack3, HitFront, HitLeft, HitRight, Death
};

USTRUCT(BlueprintType)
struct FHPMonsterActionState
{
    GENERATED_BODY()
    UPROPERTY(BlueprintReadOnly) EHPMonsterAction Action = EHPMonsterAction::None;
    UPROPERTY(BlueprintReadOnly) double ServerStartTime = 0;
    UPROPERTY(BlueprintReadOnly) int32 Revision = 0;
};

/** Custom creature rig assets. Hag's hover offset is authored in its clips. */
UCLASS(BlueprintType)
class LYRAGAME_API UHollowPinesMonsterProfile : public UDataAsset
{
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly) TObjectPtr<USkeletalMesh> Mesh;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) TSubclassOf<UAnimInstance> AnimationClass;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) TObjectPtr<UBlendSpace> Locomotion;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) TMap<EHPMonsterAction, TObjectPtr<UAnimSequence>> Actions;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) float WalkSpeed = 180;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) float RunSpeed = 400;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) float CapsuleRadius = 55;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) float CapsuleHalfHeight = 120;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) float PersonalSpace = 220;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) float MeleeReach = 220;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) bool bHover = false;
};

/** Stable spacing slots and one fair, time-limited melee animation turn per target. */
UCLASS()
class LYRAGAME_API UHollowPinesEncounter : public UWorldSubsystem
{
    GENERATED_BODY()
public:
    void Register(AHollowPinesMonster* Monster);
    void Remove(AHollowPinesMonster* Monster);
    FVector GetWaitingPosition(AHollowPinesMonster* Monster, AActor* Target) const;
    bool RequestTurn(AHollowPinesMonster* Monster, AActor* Target);
    void ReleaseTurn(AHollowPinesMonster* Monster);
    UFUNCTION(BlueprintPure) AHollowPinesMonster* GetTurnOwner(AActor* Target) const;
private:
    struct FTurn
    {
        TWeakObjectPtr<AHollowPinesMonster> Owner;
        TArray<TWeakObjectPtr<AHollowPinesMonster>> Queue;
        double Expires = 0;
    };
    TArray<TWeakObjectPtr<AHollowPinesMonster>> Monsters;
    TMap<TWeakObjectPtr<AActor>, FTurn> Turns;
};

UCLASS(Blueprintable)
class LYRAGAME_API AHollowPinesMonster : public ACharacter, public IAbilitySystemInterface, public ILyraTeamAgentInterface
{
    GENERATED_BODY()
public:
    AHollowPinesMonster();
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Monster") TObjectPtr<UHollowPinesMonsterProfile> Profile;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Monster") bool bPatrol = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Monster") float PatrolRadius = 900;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Monster") float AwarenessRadius = 2200;
    // Rehearsal is restricted to a non-pawn dummy. Player attacks/damage are not implemented.
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Animation Review") bool bRehearseAttacks = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Animation Review") TObjectPtr<AActor> PracticeTarget;
    UPROPERTY(BlueprintReadOnly, ReplicatedUsing=OnRep_Action) FHPMonsterActionState ActionState;
    UPROPERTY(BlueprintReadOnly, Replicated) bool bDead = false;
    UPROPERTY(BlueprintReadOnly, Replicated) bool bPaused = false;
    UPROPERTY(BlueprintReadOnly) TObjectPtr<ULyraHealthComponent> Health;
    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly) void PreviewAction(EHPMonsterAction Action);
    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly) void SetPaused(bool bPause);
    UFUNCTION(BlueprintPure) float GetActionAge() const;
    UFUNCTION(BlueprintPure) UAnimSequence* GetActionSequence() const;
    UFUNCTION(BlueprintPure) AActor* GetObservedTarget() const { return ObservedTarget.Get(); }
    virtual UAbilitySystemComponent* GetAbilitySystemComponent() const override;
    virtual FGenericTeamId GetGenericTeamId() const override { return FGenericTeamId(2); }
    virtual FOnLyraTeamIndexChangedDelegate* GetOnTeamIndexChangedDelegate() override { return &TeamChanged; }
    virtual void OnConstruction(const FTransform& Transform) override;
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
    virtual void Tick(float DeltaSeconds) override;
    virtual void Landed(const FHitResult& Hit) override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& Props) const override;
    bool CanRehearseWith(AActor* Target) const;
    bool IsActing() const { return ActionState.Action != EHPMonsterAction::None; }
    FTransform HomeTransform;
private:
    void SetAction(EHPMonsterAction Action);
    void Think();
    UFUNCTION() void OnRep_Action();
    UFUNCTION() void OnHealthChanged(ULyraHealthComponent* Component, float Old, float New, AActor* InstigatorActor);
    UPROPERTY() TObjectPtr<ULyraAbilitySystemComponent> AbilitySystem;
    UPROPERTY() TObjectPtr<ULyraHealthSet> HealthSet;
    UPROPERTY() FOnLyraTeamIndexChangedDelegate TeamChanged;
    TWeakObjectPtr<AActor> ObservedTarget;
    double NextThink = 0;
    double NextPatrol = 0;
    double NextTurn = 0;
    int32 AttackIndex = 0;
};

UCLASS()
class LYRAGAME_API AHollowPinesMonsterController : public AAIController
{
    GENERATED_BODY()
public:
    AHollowPinesMonsterController(const FObjectInitializer& Initializer);
};

UCLASS(Transient, Blueprintable)
class LYRAGAME_API UHollowPinesMonsterAnimInstance : public UAnimInstance
{
    GENERATED_BODY()
public:
    UPROPERTY(BlueprintReadOnly, Transient) float Speed = 0;
    UPROPERTY(BlueprintReadOnly, Transient) TObjectPtr<UAnimSequence> ActionSequence;
    UPROPERTY(BlueprintReadOnly, Transient) float ActionTime = 0;
    UPROPERTY(BlueprintReadOnly, Transient) float ActionWeight = 0;
    virtual void NativeUpdateAnimation(float DeltaSeconds) override;
};

UCLASS()
class LYRAGAME_API AHollowPinesMonsterReviewController : public ABaselinePlayerController
{
    GENERATED_BODY()
public:
    virtual void SetupInputComponent() override;
    UPROPERTY(BlueprintReadOnly) TObjectPtr<AHollowPinesMonster> SelectedMonster;
    UFUNCTION(Server, Reliable) void ServerReview(AHollowPinesMonster* Monster, int32 Command);
private:
    void SelectNext();
    void AttackOne(); void AttackTwo(); void AttackThree(); void JumpPreview(); void HitPreview(); void DeathPreview(); void ResetPreview(); void PausePreview(); void RehearsePreview();
    int32 HitIndex = 0;
    UFUNCTION(Client, Reliable) void ClientSelect(AHollowPinesMonster* Monster);
};

UCLASS()
class LYRAGAME_API AHollowPinesMonsterReviewHUD : public ABaselineHUD
{
    GENERATED_BODY()
public:
    virtual void DrawHUD() override;
};

UCLASS()
class LYRAGAME_API AHollowPinesMonsterReviewGameMode : public ACRTraversalGameMode
{
    GENERATED_BODY()
public:
    AHollowPinesMonsterReviewGameMode();
};
