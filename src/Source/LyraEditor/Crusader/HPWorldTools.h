#pragma once
#include "Kismet/BlueprintFunctionLibrary.h"
#include "HPWorldTools.generated.h"

UCLASS()
class UHPWorldTools : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    UFUNCTION(BlueprintCallable, Category="Hollow Pines|Editor")
    static bool ConfigureBiomeMeshBounds(class UBlueprint* Blueprint);
    UFUNCTION(BlueprintCallable, Category="Hollow Pines|Editor")
    static bool BuildCreatureAnimation(class UAnimBlueprint* Blueprint, class UBlendSpace* Locomotion, class UAnimSequence* Fallback);
    UFUNCTION(BlueprintCallable, Category="Hollow Pines|Editor")
    static bool ConfigureLocomotion(class UBlendSpace* BlendSpace, class UAnimSequence* Idle, class UAnimSequence* Walk, class UAnimSequence* Run, float WalkSpeed, float RunSpeed);
    UFUNCTION(BlueprintCallable, Category="Hollow Pines|Editor")
    static class ANavMeshBoundsVolume* AddNavigationBounds(UWorld* World, FVector Center, FVector Size);
    UFUNCTION(BlueprintCallable, Category="Hollow Pines|Editor")
    static FString BuildNavigation(UWorld* World);
    UFUNCTION(BlueprintCallable, Category="Hollow Pines|Editor")
    static AActor* CreateMeshTerrain(UWorld* World, UObject* Definition);
    UFUNCTION(BlueprintCallable, Category="Hollow Pines|Editor")
    static AActor* AddMeshTerrainSection(AActor* Terrain, class UDynamicMesh* Mesh, const FString& Label);
    UFUNCTION(BlueprintCallable, Category="Hollow Pines|Editor")
    static class UDynamicMesh* GetMeshTerrainSection(AActor* Section);
    UFUNCTION(BlueprintCallable, Category="Hollow Pines|Editor")
    static FString CleanMeshTerrainWeights(AActor* Section);
    UFUNCTION(BlueprintCallable, Category="Hollow Pines|Editor")
    static bool ConfigureGorePainter(class UBlueprint* Blueprint);
};
