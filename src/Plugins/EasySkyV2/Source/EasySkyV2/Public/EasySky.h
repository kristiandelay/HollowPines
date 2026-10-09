// EasySkyV2, Copyright 2023 PS Studios

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Components/DirectionalLightComponent.h"
#include "Components/ExponentialHeightFogComponent.h"
#include "Materials/MaterialParameterCollectionInstance.h"
#include "Components/SkyLightComponent.h"
#include "UObject/NameTypes.h"
#include "Engine/TextureRenderTarget2D.h"
#include "Components/SceneCaptureComponent2D.h"
#include "ComponentReregisterContext.h"
#include "RHIResources.h"
#include "TextureResource.h"
#include "Math/BoxSphereBounds.h"

#include "EasySky.generated.h"

UCLASS(ClassGroup = (Custom), meta = (BlueprintSpawnableComponent), hidecategories = ("Replication", "Collision", "Input", "Actor", "LOD", "Cooking", "Hidden"))
class AEasySkyV2 : public AActor
{
		GENERATED_BODY()

public:

	/* Allows Tick To happen in the editor viewport*/
	virtual bool ShouldTickIfViewportsOnly() const override;
	virtual void Tick(float DeltaTime) override;

	UFUNCTION(BlueprintImplementableEvent, Category = "EasySkyV2")
		void AddRemoveTemperatureZone(const bool Add, const ATemperatureZone* TemperatureZoneActor);

	UFUNCTION(BlueprintCallable, Category = "EasySkyV2")
		void callAddRemoveTemperatureZone(const bool Add, const ATemperatureZone* TemperatureZoneActor);

	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Editor Preview")
		bool enableEditorTick = true;

	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Editor Preview")
		bool realTimeDynamicWeatherInEditor = false;

	UPROPERTY()
		bool ShouldUpdateTemperatureTexture = false;

	UFUNCTION(BlueprintCallable, Category = "EasySkyV2")
		void SortTemperatureZones();

	// Set Directional light Forward Shading Priorities
	UFUNCTION(BlueprintCallable, Category = "EasySkyV2")
		void SetLightComponentProperties(UDirectionalLightComponent* Sunlight, UDirectionalLightComponent* Moonlight, UDirectionalLightComponent* MovableThunderLight, UDirectionalLightComponent* StationaryThunderLight, USceneCaptureComponent2D* CaptureComponent);

	UFUNCTION(BlueprintCallable, Category = "EasySkyV2")
		void SetSourceSoftAngle(UDirectionalLightComponent* DirectionalLight, float SourceSoftAngle);

	UFUNCTION(BlueprintCallable, Category = "EasySkyV2")
		void RefreshSceneComponent(USceneComponent* SceneComponent);

	UFUNCTION(BlueprintCallable, Category = "EasySkyV2")
		void CreateTextureFrom32BitFloat(UTextureRenderTarget2D* RenderTarget, TArray<float> data, int width, int height);

	UFUNCTION(BlueprintCallable, Category = "EasySkyV2")
		void SetRenderTargetSize(UTextureRenderTarget2D* RenderTarget, int32 value);

	UFUNCTION(BlueprintCallable, Category = "Settings")
		void SetCollectionParameterScalar(UMaterialParameterCollectionInstance* CollectionInstance, FName ParameterName, float ParameterValue);

	/* Tick that runs ONLY in the editor viewport.*/
	UFUNCTION(BlueprintImplementableEvent, CallInEditor, Category = "Settings")
		void BlueprintEditorTick(float DeltaTime);

	UFUNCTION(BlueprintCallable, Category = "EasySkyV2")
		FVector GetViewLocation();

	UFUNCTION(BlueprintCallable, Category = "EasySkyV2")
		void SetVolumetricFogGridPixelSize(int32 VolumetricFogGridPixelSize);

	UFUNCTION(BlueprintCallable, Category = "EasySkyV2")
		void SetConsoleVariable(FString Property, int32 Value);

	UFUNCTION(BlueprintCallable, Category = "EasySkyV2")
		void SetRealTimeCapture(USkyLightComponent* SkyLightComponent, bool enabled);

	UFUNCTION(BlueprintCallable, Category = "EasySkyV2")
		void AddMaterialFunction(UMaterial* mat, UMaterialFunction* MaterialFunction, FName FunctionInputName, FName FunctionOutputName);

	UFUNCTION(BlueprintPure, Category = "EasySkyV2")
		bool IsWithEditor() const
		{
		#if WITH_EDITOR
				return true;
		#else
				return false;
		#endif
			}

	UFUNCTION(BlueprintCallable, Category = "EasySkyV2")
		bool CreateTemperatureTexture();

	// If true, rain and snow won't be visible under the height defined at CollisionFloorLevel.
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Weather")
		bool UseCollisionFloorLevel = false;

	// The height under which rain and snow will be rendered invisible.
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Weather", meta = (EditCondition = "UseCollisionFloorLevel"))
		float CollisionFloorLevel = 0.0;

	// The distance in unreal units (cm) to fade out the puddles, rain and snow.
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Weather", meta = (EditCondition = "UseCollisionFloorLevel"))
		float CollisionFloorFadeDistance = 1.0;

	// Flag to show the debug visualization of the temperature ingame.
	UPROPERTY(BlueprintReadWrite, Category = "Temperature", EditAnywhere)//, meta = (EditCondition = "bUseTemperatureSystem && Initialized"))
		bool bShowTemperatureDebugDraw = false;

	// The opacity of the debug draw preview for the temperature.
	UPROPERTY(BlueprintReadWrite, Category = "Temperature", EditAnywhere, meta = (UIMin = "0.0", UIMax = "1.0")) // EditCondition = "bUseTemperatureSystem && Initialized", 
		float DebugDrawOpacity = 0.75;

	// The temperature at which snow starts to form. Temperature is in degrees celsius.
	UPROPERTY(BlueprintReadWrite, Category = "Temperature", EditAnywhere, meta = (UIMin = "-10", UIMax = "0")) // EditCondition = "bUseTemperatureSystem && Initialized", 
		float SnowStartTemperature = 0.0;

	// The amount of temperature difference needed to go from rain to snow.
	UPROPERTY(BlueprintReadWrite, Category = "Temperature", EditAnywhere, meta = (UIMin = "0", UIMax = "10")) // EditCondition = "bUseTemperatureSystem && Initialized", 
		float SnowBlendSize = 4.0;

	UPROPERTY(BlueprintReadWrite, Category = "Hidden", EditAnywhere, meta = (EditCondition = "false"))
		TArray<TObjectPtr<ATemperatureZone>> TemperatureZones;

	UFUNCTION(BlueprintCallable, Category = "EasySkyV2")
		void AddRemoveTemperatureZoneFunc(ATemperatureZone* TemperatureZone, bool Add);

	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Hidden")
		TObjectPtr<UTextureRenderTarget2D> RenderTargetTemperatureVolumes;

protected:

	UPROPERTY()
		int TickCounter = 0;

};