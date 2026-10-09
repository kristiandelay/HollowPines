#pragma once

#include "Player/LyraPlayerState.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "HollowPinesPlayerState.generated.h"

/** Character identity belongs to the player, so death does not reshuffle the team. */
UCLASS()
class LYRAGAME_API AHollowPinesPlayerState : public ALyraPlayerState
{
    GENERATED_BODY()
public:
    UPROPERTY(Replicated, BlueprintReadOnly, Category="Hollow Pines|Character")
    TSoftClassPtr<AActor> AssignedVisualOverride;
    virtual void CopyProperties(APlayerState* PlayerState) override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
};

UCLASS()
class LYRAGAME_API UHollowPinesGameplayLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    UFUNCTION(BlueprintCallable, Category="Hollow Pines|Character")
    static TSoftClassPtr<AActor> ResolvePlayerVisualOverride(AActor* PawnOwner,
        const TArray<TSoftClassPtr<AActor>>& AvailableVisuals, TSoftClassPtr<AActor> FallbackVisual);
    UFUNCTION(BlueprintCallable, Category="Hollow Pines|Traversal")
    static void TrackTraversal(UActorComponent* TraversalLogic, class UAnimMontage* Montage, class UPrimitiveComponent* Obstacle);
    UFUNCTION(BlueprintCallable, Category="Hollow Pines|Traversal")
    static void FinishTraversal(UActorComponent* TraversalLogic);
};
