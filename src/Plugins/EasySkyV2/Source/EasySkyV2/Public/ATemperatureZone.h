// EasySkyV2, Copyright 2022 PS Studios

#pragma once
#include "EasySky.h"
#include "Components/SphereComponent.h"
#include "Components/SceneComponent.h"
#include "Components/BoxComponent.h"
#include "ATemperatureZone.generated.h"

UENUM(BlueprintType)
enum class ESVolumeType : uint8 {
	SPHERE UMETA(DisplayName = "Sphere"),
	BOX UMETA(DisplayName = "Box")
};

UENUM(BlueprintType)
enum class EESTemperatureType : uint8 {
	FIXED UMETA(DisplayName = "Fixed Temperature"),
	DIFFERENCE UMETA(DisplayName = "Temperature Difference")
};

UCLASS(ClassGroup = (Custom), meta = (BlueprintSpawnableComponent), hidecategories = ("Replication", "Collision", "Input", "Actor", "LOD", "Cooking", "Hidden"))
class ATemperatureZone : public AActor
{
	GENERATED_BODY()

public:

	ATemperatureZone();

	virtual void Destroyed() override;
	virtual void OnConstruction(const FTransform& Transform) override;

	UPROPERTY(BlueprintReadOnly, VisibleAnywhere, Category = "Components")
		TObjectPtr<USceneComponent> SceneComponent;
	UPROPERTY(BlueprintReadOnly, VisibleAnywhere, Category = "Components")
		TObjectPtr<USphereComponent> SphereComponent;
	UPROPERTY(BlueprintReadOnly, VisibleAnywhere, Category = "Components")
		TObjectPtr<UBoxComponent> BoxComponent;

	UFUNCTION(BlueprintCallable, Category = "Temperature")
		void callAddRemoveTemperatureZone(bool Add, ATemperatureZone* TemperatureZone);

	// The shape of the volume. Sphere volumes are a bit cheaper than box volumes.
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Temperature")
		ESVolumeType VolumeType;

	// The way of handeling temperature. Fixed Temperature means it will set the volume to a fixed temperature. Additive Temperature will add the temperature value as if it were a difference.
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Temperature")
		EESTemperatureType TemperatureType = EESTemperatureType::DIFFERENCE;

	// The temperature of this volume. If TemperatureType is set to Fixed Temperature, this will be the fixed temperature in this zone. When set to Temperature Difference, this temperature will be threated as a difference over the current temperature. Volumes are always sorted by priority. Temperature in Degrees Celcius.
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Temperature")
		float Temperature = 5.0;

	// Priority of the Temperature Volume. A higher priority will be calculated last. The lowest priority will be calculated first.
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Temperature")
		int Priority = 0;

	// The power of the fadeout.
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Temperature", meta = (ClampMin = "0.01", UIMin = "0.01", UIMax = "5.0"))
		float Power = 1.0;

	// The hardness of the box gradient.
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Temperature", meta = (EditCondition = "VolumeType == ESVolumeType::BOX", ClampMin = "0.01", UIMin = "0.01", UIMax = "5.0"))
		float Hardness = 1.0;

	UPROPERTY(BlueprintReadWrite, Category = "Hidden")
		TObjectPtr<AEasySkyV2> EasySkyActor;

};