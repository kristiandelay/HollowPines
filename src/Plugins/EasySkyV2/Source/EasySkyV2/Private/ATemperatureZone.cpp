// EasySkyV2, Copyright 2023 PS Studios

#include "ATemperatureZone.h"
#include "Kismet/GameplayStatics.h"

ATemperatureZone::ATemperatureZone()
{
	SceneComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root Scene Component"));
	SphereComponent = CreateDefaultSubobject<USphereComponent>(TEXT("Sphere"));
	SphereComponent->SetupAttachment(SceneComponent);
	SphereComponent->SetRelativeLocation(FVector(0.0, 0.0, 0.0));
	BoxComponent = CreateDefaultSubobject<UBoxComponent>(TEXT("Box"));
	BoxComponent->SetupAttachment(SceneComponent);
	BoxComponent->SetRelativeLocation(FVector(0.0, 0.0, 0.0));
}

void ATemperatureZone::callAddRemoveTemperatureZone(bool Add, ATemperatureZone* TemperatureZone)
{
	if (ATemperatureZone::EasySkyActor == nullptr)
	{
		TArray<AActor*> FoundActors;
		UGameplayStatics::GetAllActorsOfClass(GetWorld(), AEasySkyV2::StaticClass(), FoundActors);
		if (FoundActors.Num() == 0)
		{
			return;
		}
		else
		{
			EasySkyActor = Cast<AEasySkyV2>(FoundActors[0]);
		}
	}
	ATemperatureZone::EasySkyActor->AddRemoveTemperatureZoneFunc(this, Add);
}

void ATemperatureZone::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);
	if (VolumeType == ESVolumeType::SPHERE)
	{
		if (IsValid(BoxComponent) && IsValid(SphereComponent))
		{
			BoxComponent->SetVisibility(false);
			SphereComponent->SetVisibility(true);
		}
	}
	else
	{
		if (IsValid(BoxComponent) && IsValid(SphereComponent))
		{
			SphereComponent->SetVisibility(false);
			BoxComponent->SetVisibility(true);
		}
	}
	callAddRemoveTemperatureZone(true, this);
}

void ATemperatureZone::Destroyed()
{
	ATemperatureZone::callAddRemoveTemperatureZone(false, this);
	Super::Destroyed();
}
