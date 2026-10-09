#include "HollowPinesPlayerState.h"
#include "Baseline/BaselineCharacterMovement.h"
#include "GameFramework/Character.h"
#include "GameFramework/GameStateBase.h"
#include "GameFramework/PlayerController.h"
#include "HAL/IConsoleManager.h"
#include "Net/UnrealNetwork.h"

static TAutoConsoleVariable<int32> CVarUniquePlayerVisuals(TEXT("hp.UniquePlayerVisuals"), 1,
    TEXT("Assign distinct characters on the server. Set to 0 for the sample visual preview widget."));

void AHollowPinesPlayerState::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AHollowPinesPlayerState, AssignedVisualOverride);
}

void AHollowPinesPlayerState::CopyProperties(APlayerState* PlayerState)
{
    Super::CopyProperties(PlayerState);
    if (auto* Other = Cast<AHollowPinesPlayerState>(PlayerState))
        Other->AssignedVisualOverride = AssignedVisualOverride;
}

TSoftClassPtr<AActor> UHollowPinesGameplayLibrary::ResolvePlayerVisualOverride(AActor* PawnOwner,
    const TArray<TSoftClassPtr<AActor>>& AvailableVisuals, TSoftClassPtr<AActor> FallbackVisual)
{
    if (!PawnOwner || !PawnOwner->HasAuthority() || !CVarUniquePlayerVisuals.GetValueOnGameThread()) return FallbackVisual;
    const auto* Pawn = Cast<APawn>(PawnOwner);
    if (!Pawn) return FallbackVisual;
    // BeginPlay runs before possession. PossessedBy requests the visual again.
    // Do not start an async preview load which could overwrite that assignment later.
    if (!Pawn->GetController()) return {};
    if (!Cast<APlayerController>(Pawn->GetController())) return FallbackVisual;
    auto* State = Pawn->GetPlayerState<AHollowPinesPlayerState>();
    const auto* GameState = Pawn->GetWorld()->GetGameState();
    if (!State || !GameState) return FallbackVisual;

    TArray<TSoftClassPtr<AActor>> Pool;
    for (bool bSurvivors : {true, false})
        for (const auto& Visual : AvailableVisuals)
            if (!Visual.IsNull() && Visual.ToSoftObjectPath().ToString().StartsWith(TEXT("/Game/HollowPines/Players/")) == bSurvivors)
                Pool.AddUnique(Visual);
    if (Pool.IsEmpty()) return FallbackVisual;

    TMap<FSoftObjectPath, int32> Usage;
    for (const auto& Player : GameState->PlayerArray)
        if (const auto* Other = Cast<AHollowPinesPlayerState>(Player);
            Other && Other != State && Other->GetPlayerConnectionType() == ELyraPlayerConnectionType::Player)
            if (!Other->AssignedVisualOverride.IsNull()) ++Usage.FindOrAdd(Other->AssignedVisualOverride.ToSoftObjectPath());

    // Reservations are synchronous on the server, before the Blueprint async load.
    if (Pool.Contains(State->AssignedVisualOverride))
        return State->AssignedVisualOverride;
    auto Selected = Pool[0];
    for (const auto& Visual : Pool)
        if (Usage.FindRef(Visual.ToSoftObjectPath()) < Usage.FindRef(Selected.ToSoftObjectPath())) Selected = Visual;
    State->AssignedVisualOverride = Selected;
    State->ForceNetUpdate();
    return Selected;
}

void UHollowPinesGameplayLibrary::TrackTraversal(UActorComponent* TraversalLogic, UAnimMontage* Montage, UPrimitiveComponent* Obstacle)
{
    if (auto* Character = TraversalLogic ? Cast<ACharacter>(TraversalLogic->GetOwner()) : nullptr)
        if (auto* Movement = Cast<UBaselineCharacterMovement>(Character->GetCharacterMovement()))
            Movement->TrackTraversal(TraversalLogic, Montage, Obstacle);
}

void UHollowPinesGameplayLibrary::FinishTraversal(UActorComponent* TraversalLogic)
{
    if (auto* Character = TraversalLogic ? Cast<ACharacter>(TraversalLogic->GetOwner()) : nullptr)
        if (auto* Movement = Cast<UBaselineCharacterMovement>(Character->GetCharacterMovement())) Movement->FinishTraversal();
}
