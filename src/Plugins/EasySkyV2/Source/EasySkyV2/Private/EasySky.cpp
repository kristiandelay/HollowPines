// EasySkyV2, Copyright 2023 PS Studios

#include "EasySky.h"
#ifndef ENGINE_MAJOR_VERSION
	#include "Runtime/Launch/Resources/Version.h"
#endif

#if WITH_EDITOR
	#include "Materials/MaterialExpressionMakeMaterialAttributes.h"
	#include "MaterialExpressionIO.h"
	#include "Materials/MaterialExpressionMaterialFunctionCall.h"
	#include "Materials/MaterialExpressionFunctionInput.h"
#endif

#include "ATemperatureZone.h"

void AEasySkyV2::SortTemperatureZones()
{
	
	TArray<TObjectPtr<ATemperatureZone>> temperature_zones;

	for (int i = 0; i < TemperatureZones.Num(); i++)
	{
		bool Added = false;
		for (int j = 0; j < temperature_zones.Num(); j++)
		{
			if (IsValid(temperature_zones[j]))
			{
				if (temperature_zones[j]->Priority >= TemperatureZones[i]->Priority)
				{
					temperature_zones.Insert(TemperatureZones[i], j);
					Added = true;
					break;
				}
			}
		}
		if (!Added)
		{
			temperature_zones.Add(TemperatureZones[i]);
		}
		
	}
	TemperatureZones = temperature_zones;
}

void AEasySkyV2::callAddRemoveTemperatureZone(const bool Add, const ATemperatureZone* TemperatureZoneActor)
{
	this->AddRemoveTemperatureZone(Add, TemperatureZoneActor);
}

void AEasySkyV2::CreateTextureFrom32BitFloat(UTextureRenderTarget2D* RenderTarget, TArray<float> data, int width, int height) {

	if (RenderTarget == nullptr)
	{
		return;
	}
#if ENGINE_MAJOR_VERSION == 4
	FTextureResource* texture_resource = RenderTarget->Resource;
#else
	FTextureResource* texture_resource = RenderTarget->GetResource();
#endif
	if (texture_resource == nullptr)
	{
		return;
	}
#if ENGINE_MAJOR_VERSION == 4 || ENGINE_MAJOR_VERSION == 5 && ENGINE_MINOR_VERSION == 0 // Version 4.x and 5.0
	FRHITexture2D* FRHI = texture_resource->GetTexture2DRHI();
#elif ENGINE_MAJOR_VERSION == 5 && ENGINE_MINOR_VERSION == 1 // Version 5.1
	FRHITexture2D* FRHI = texture_resource->GetTexture2DRHI();
#else // Version 5.2+
	FRHITexture* FRHI = texture_resource->GetTextureRHI().GetReference();
#endif

	ENQUEUE_RENDER_COMMAND(CreateTextureFrom32BitFloat)(
		[=](FRHICommandListImmediate& RHICmdList)
		{
			RHIUpdateTexture2D(
				FRHI,
				0,
				FUpdateTextureRegion2D(0, 0, 0, 0, width, height),
				width * data.GetTypeSize(),
				reinterpret_cast<const uint8*>(data.GetData())
			);
		});
	FlushRenderingCommands();

	// Update the render target to fix the first frame issue in the editor.
	ShouldUpdateTemperatureTexture = true;
	return;

}

void AEasySkyV2::Tick(float DeltaTime)
{
	// Update the render target after frame 1 in the editor to fix the first frame issue.
	if (ShouldUpdateTemperatureTexture)
	{
		if (TickCounter == 1 && ShouldUpdateTemperatureTexture && GetWorld() != nullptr)
		{
			ShouldUpdateTemperatureTexture = false;
#if WITH_EDITOR
			CreateTemperatureTexture();
#endif
		}
		TickCounter += 1;
	}

	if (GetWorld() != nullptr && GetWorld()->WorldType == EWorldType::Editor)
	{
#if WITH_EDITOR
		BlueprintEditorTick(DeltaTime);
#endif
	}
	else
	{
		Super::Tick(DeltaTime);
	}
}

bool AEasySkyV2::CreateTemperatureTexture()
{
	SortTemperatureZones();
	float NumOfSpheres = 0.0;
	float NumOfBoxes = 0.0;
	TArray<float> CombinedFloatArray;
	int height = 0;

	for (int i = 0; i < TemperatureZones.Num(); i++)
	{
		ATemperatureZone* CurrentVolume = TemperatureZones[i];
		if (IsValid(CurrentVolume))
		{
			if (CurrentVolume->VolumeType == ESVolumeType::SPHERE)
			{
				NumOfSpheres += 1.0;
			}
			else
			{
				NumOfBoxes += 1.0;
			}
		}
	}

	CombinedFloatArray.Add(NumOfBoxes);
	// Fill the rest of the line with empty values
	for (int i = 0; i < 12; ++i)
	{
		CombinedFloatArray.Add(0.0);
	}
	height += 1;
	CombinedFloatArray.Add(NumOfSpheres);
	// Fill the rest of the line with empty values
	for (int i = 0; i < 12; ++i)
	{
		CombinedFloatArray.Add(0.0);
	}
	height += 1;
	
	for (int i = 0; i < TemperatureZones.Num(); i++)
	{
		ATemperatureZone* CurrentVolume = TemperatureZones[i];
		if (IsValid(CurrentVolume) && IsValid(CurrentVolume->BoxComponent) && IsValid(CurrentVolume->SphereComponent))
		{
			if (CurrentVolume->VolumeType == ESVolumeType::SPHERE)
			{
				// Volume type
				CombinedFloatArray.Add(1.0);
				FVector SphereLocation = CurrentVolume->SphereComponent->GetComponentLocation();
				// Location, Radius, Power, Value, TemperatureType, Hardness
				CombinedFloatArray.Add(SphereLocation.X);
				CombinedFloatArray.Add(SphereLocation.Y);
				CombinedFloatArray.Add(SphereLocation.Z);
				CombinedFloatArray.Add(CurrentVolume->SphereComponent->GetScaledSphereRadius());
				CombinedFloatArray.Add(CurrentVolume->Power);
				CombinedFloatArray.Add(CurrentVolume->Temperature);
				if (CurrentVolume->TemperatureType == EESTemperatureType::DIFFERENCE)
					CombinedFloatArray.Add(1.0);
				else
					CombinedFloatArray.Add(0.0);

				//CombinedFloatArray.Add(CurrentVolume->Hardness);
				CombinedFloatArray.Add(0.0); // Hardness is not used so we fill it with a const 0.0

				// Fill the array with empty values to match the length of box array values.
				CombinedFloatArray.Add(0.0);
				CombinedFloatArray.Add(0.0);
				CombinedFloatArray.Add(0.0);
				CombinedFloatArray.Add(0.0);
			}

			else
			{
				// Volume type
				CombinedFloatArray.Add(2.0);
				FVector BoxLocation = CurrentVolume->BoxComponent->GetComponentLocation();
				CombinedFloatArray.Add(BoxLocation.X);
				CombinedFloatArray.Add(BoxLocation.Y);
				CombinedFloatArray.Add(BoxLocation.Z);
				FVector BoxExtend = CurrentVolume->BoxComponent->GetScaledBoxExtent();
				CombinedFloatArray.Add(BoxExtend.X);
				CombinedFloatArray.Add(BoxExtend.Y);
				CombinedFloatArray.Add(BoxExtend.Z);
				FVector ForwardVector = CurrentVolume->BoxComponent->GetForwardVector();
				ForwardVector *= FVector(1.0, 1.0, 0.0);
				ForwardVector.Normalize(0.0001);
				CombinedFloatArray.Add(ForwardVector.X);
				CombinedFloatArray.Add(ForwardVector.Y);

				CombinedFloatArray.Add(CurrentVolume->Power);
				CombinedFloatArray.Add(CurrentVolume->Temperature);
				CombinedFloatArray.Add(CurrentVolume->Hardness);
				if (CurrentVolume->TemperatureType == EESTemperatureType::DIFFERENCE)
					CombinedFloatArray.Add(1.0);
				else
					CombinedFloatArray.Add(0.0);
			}
			height += 1;
		}
	}

	CreateTextureFrom32BitFloat(RenderTargetTemperatureVolumes, CombinedFloatArray, 13, height);

	return true;
}


void AEasySkyV2::AddRemoveTemperatureZoneFunc(ATemperatureZone* TemperatureZone, bool Add)
{
	if (IsValid(TemperatureZone))
	{
		if (Add)
		{
			if (AEasySkyV2::TemperatureZones.Find(TemperatureZone) == INDEX_NONE)
			{
				// Add element
				AEasySkyV2::TemperatureZones.Add(TemperatureZone);
			}
		}
		else
		{
			if (TemperatureZones.Find(TemperatureZone) != INDEX_NONE)
			{
				// Remove
				AEasySkyV2::TemperatureZones.Remove(TemperatureZone);
			}
		}
		// Refresh the Temperature Texture
		CreateTemperatureTexture();
	}
}


bool AEasySkyV2::ShouldTickIfViewportsOnly() const
{
	if (GetWorld() != nullptr && GetWorld()->WorldType == EWorldType::Editor && enableEditorTick)
	{
		return true;
	}
	else
	{
		return false;
	}
}

/*Get the view location of the camera. This works for the editor as well as for the game.*/
FVector AEasySkyV2::GetViewLocation()
{
	auto world = GetWorld();
	FVector CamLocation;
	if (world == nullptr)
		return CamLocation;

	auto viewLocations = world->ViewLocationsRenderedLastFrame;
	if (viewLocations.Num() == 0)
		return CamLocation;

	CamLocation = viewLocations[0];
	return(CamLocation);
}

void AEasySkyV2::SetRenderTargetSize(UTextureRenderTarget2D* RenderTarget, int32 value)
{
	if (RenderTarget && value != 0)
	{
		RenderTarget->ResizeTarget(value, value);
	}
}

void AEasySkyV2::SetSourceSoftAngle(UDirectionalLightComponent* DirectionalLight, float SourceSoftAngle)
{
	DirectionalLight->LightSourceSoftAngle = SourceSoftAngle;
	DirectionalLight->SetVisibility(false);
	DirectionalLight->SetVisibility(true);
}

void AEasySkyV2::SetCollectionParameterScalar(UMaterialParameterCollectionInstance* CollectionInstance, FName ParameterName, float ParameterValue)
{
	CollectionInstance->SetScalarParameterValue(ParameterName, ParameterValue);
}

void AEasySkyV2::SetVolumetricFogGridPixelSize(int32 VolumetricFogGridPixelSize)
{
	IConsoleVariable* CVar = IConsoleManager::Get().FindConsoleVariable(TEXT("r.VolumetricFog.GridPixelSize"));
	CVar->Set(VolumetricFogGridPixelSize, ECVF_SetByGameSetting);
}

void AEasySkyV2::SetConsoleVariable(FString Property, int32 Value)
{
	IConsoleVariable* CVar = IConsoleManager::Get().FindConsoleVariable(*Property);
	CVar->Set(Value, ECVF_SetByGameSetting);
}

void AEasySkyV2::SetRealTimeCapture(USkyLightComponent* SkyLightComponent, bool enabled)
{
	SkyLightComponent->bRealTimeCapture = enabled;
}

void AEasySkyV2::RefreshSceneComponent(USceneComponent* SceneComponent)
{
	bool OldVis = SceneComponent->IsVisible();
	SceneComponent->SetVisibility(!OldVis);
	SceneComponent->SetVisibility(OldVis);
}

void AEasySkyV2::SetLightComponentProperties(UDirectionalLightComponent* Sunlight, UDirectionalLightComponent* Moonlight, UDirectionalLightComponent* MovableThunderLight, UDirectionalLightComponent* StationaryThunderLight, USceneCaptureComponent2D* CaptureComponent)
{
	// Set Forward Shading priority if the engine version is higher than 5.1
#if (ENGINE_MAJOR_VERSION == 5 && ENGINE_MINOR_VERSION >= 1)
	if (Sunlight != nullptr)
		Sunlight->ForwardShadingPriority = 2;
	if (Moonlight != nullptr)
		Moonlight->ForwardShadingPriority = 1;
	if (MovableThunderLight != nullptr)
	{
		MovableThunderLight->ForwardShadingPriority = 0;
		MovableThunderLight->bAtmosphereSunLight = 0;
	}
	if (StationaryThunderLight != nullptr)
	{
		StationaryThunderLight->ForwardShadingPriority = 0;
		StationaryThunderLight->bAtmosphereSunLight = 0;
	}
	if (CaptureComponent != nullptr)
		CaptureComponent->bAlwaysPersistRenderingState = true;
#endif
}

void AEasySkyV2::AddMaterialFunction(UMaterial* UnrealMaterial, UMaterialFunction* MaterialFunction, FName FunctionInputName, FName FunctionOutputName)
{
#if WITH_EDITOR
	TArray<UTexture*> textures;
	TArray<UTexture*> validTextures;
	UMaterialExpression* MAInput;
	int32 NodePosX = UnrealMaterial->GetMaterial()->GetBaseMaterial()->EditorX;
	int32 NodePosY = UnrealMaterial->GetMaterial()->GetBaseMaterial()->EditorY;

	// Engine version 5.1.0 uses EditorOnlyData to store expressions.
#if (ENGINE_MAJOR_VERSION == 4 || (ENGINE_MAJOR_VERSION == 5 && ENGINE_MINOR_VERSION == 0))
	UMaterial* EditorData = UnrealMaterial->GetMaterial()->GetBaseMaterial();
#else
	UMaterialEditorOnlyData* EditorData = UnrealMaterial->GetMaterial()->GetBaseMaterial()->GetEditorOnlyData();
#endif

	if (UnrealMaterial->bUseMaterialAttributes == true)
	{
		MAInput = EditorData->MaterialAttributes.Expression;
		UMaterialExpressionMaterialFunctionCall* MatFuncCast = Cast<UMaterialExpressionMaterialFunctionCall>(MAInput);
		if (MatFuncCast != nullptr)
		{
			UMaterialFunctionInterface* UsedMatFunction = MatFuncCast->MaterialFunction;
			if (UsedMatFunction == MaterialFunction)
				return;
		}
		else
		{
			UnrealMaterial->GetMaterial()->GetBaseMaterial()->EditorX = NodePosX + 200;
		}
	}
	else
	{
		UMaterialExpression* BaseColorInput = EditorData->BaseColor.Expression;
		UMaterialExpression* MetallicInput = EditorData->Metallic.Expression;
		UMaterialExpression* SpecularInput = EditorData->Specular.Expression;
		UMaterialExpression* RoughnessInput = EditorData->Roughness.Expression;
		UMaterialExpression* AnisotropyInput = EditorData->Anisotropy.Expression;
		UMaterialExpression* EmissiveInput = EditorData->EmissiveColor.Expression;
		UMaterialExpression* OpacityInput = EditorData->Opacity.Expression;
		UMaterialExpression* OpacityMaskInput = EditorData->OpacityMask.Expression;
		UMaterialExpression* NormalInput = EditorData->Normal.Expression;
		UMaterialExpression* TangentInput = EditorData->Tangent.Expression;
		UMaterialExpression* WPOInput = EditorData->WorldPositionOffset.Expression;
		UMaterialExpression* SubsurfaceColorInput = EditorData->SubsurfaceColor.Expression;
		UMaterialExpression* AOInput = EditorData->AmbientOcclusion.Expression;
		UMaterialExpression* RefractionInput = EditorData->Refraction.Expression;
		UMaterialExpression* PDOInput = EditorData->PixelDepthOffset.Expression;
		UMaterialExpression* CustomizedUVs0Input = EditorData->CustomizedUVs[0].Expression;
		UMaterialExpression* CustomizedUVs1Input = EditorData->CustomizedUVs[1].Expression;
		UMaterialExpression* CustomizedUVs2Input = EditorData->CustomizedUVs[2].Expression;
		UMaterialExpression* CustomizedUVs3Input = EditorData->CustomizedUVs[3].Expression;
		UMaterialExpression* CustomizedUVs4Input = EditorData->CustomizedUVs[4].Expression;
		UMaterialExpression* CustomizedUVs5Input = EditorData->CustomizedUVs[5].Expression;
		UMaterialExpression* CustomizedUVs6Input = EditorData->CustomizedUVs[6].Expression;
		UMaterialExpression* CustomizedUVs7Input = EditorData->CustomizedUVs[7].Expression;
		UMaterialExpression* CustomizedUVs8Input = EditorData->CustomizedUVs[8].Expression;


		// Don't get WorldDisplacement or TesselationMultiplier in UE5 as they are depricated.
#if ENGINE_MAJOR_VERSION == 4
		UMaterialExpression* WorldDisplacementInput = UnrealMaterial->GetMaterial()->GetBaseMaterial()->WorldDisplacement.Expression;
		UMaterialExpression* TMInput = UnrealMaterial->GetMaterial()->GetBaseMaterial()->TessellationMultiplier.Expression;
#endif

		UMaterialExpressionMakeMaterialAttributes* MatAttr = NewObject<UMaterialExpressionMakeMaterialAttributes>(UnrealMaterial);

		// Engine version 5.1.0 branching
#if (ENGINE_MAJOR_VERSION == 4 || (ENGINE_MAJOR_VERSION == 5 && ENGINE_MINOR_VERSION == 0))
		UnrealMaterial->Expressions.Add(MatAttr);
#else		
		EditorData->ExpressionCollection.Expressions.Add(MatAttr);
#endif

		if (BaseColorInput != nullptr)
			MatAttr->BaseColor.Connect(EditorData->BaseColor.OutputIndex, BaseColorInput);
		if (MetallicInput != nullptr)
			MatAttr->Metallic.Connect(EditorData->Metallic.OutputIndex, MetallicInput);
		if (SpecularInput != nullptr)
			MatAttr->Specular.Connect(EditorData->Specular.OutputIndex, SpecularInput);
		if (RoughnessInput != nullptr)
			MatAttr->Roughness.Connect(EditorData->Roughness.OutputIndex, RoughnessInput);
		if (AnisotropyInput != nullptr)
			MatAttr->Anisotropy.Connect(EditorData->Anisotropy.OutputIndex, AnisotropyInput);
		if (EmissiveInput != nullptr)
			MatAttr->EmissiveColor.Connect(EditorData->EmissiveColor.OutputIndex, EmissiveInput);
		if (OpacityInput != nullptr)
			MatAttr->Opacity.Connect(EditorData->Opacity.OutputIndex, OpacityInput);
		if (OpacityMaskInput != nullptr)
			MatAttr->OpacityMask.Connect(EditorData->OpacityMask.OutputIndex, OpacityMaskInput);
		if (NormalInput != nullptr)
			MatAttr->Normal.Connect(EditorData->Normal.OutputIndex, NormalInput);
		if (TangentInput != nullptr)
			MatAttr->Tangent.Connect(EditorData->Tangent.OutputIndex, TangentInput);
		if (WPOInput != nullptr)
			MatAttr->WorldPositionOffset.Connect(EditorData->WorldPositionOffset.OutputIndex, WPOInput);
		if (SubsurfaceColorInput != nullptr)
			MatAttr->SubsurfaceColor.Connect(EditorData->SubsurfaceColor.OutputIndex, SubsurfaceColorInput);
		if (AOInput != nullptr)
			MatAttr->AmbientOcclusion.Connect(EditorData->AmbientOcclusion.OutputIndex, AOInput);
		if (RefractionInput != nullptr)
			MatAttr->Refraction.Connect(EditorData->Refraction.OutputIndex, RefractionInput);
		if (PDOInput != nullptr)
			MatAttr->PixelDepthOffset.Connect(EditorData->PixelDepthOffset.OutputIndex, PDOInput);
		if (CustomizedUVs0Input != nullptr)
			MatAttr->CustomizedUVs[0].Connect(EditorData->CustomizedUVs[0].OutputIndex, CustomizedUVs0Input);
		if (CustomizedUVs1Input != nullptr)
			MatAttr->CustomizedUVs[1].Connect(EditorData->CustomizedUVs[1].OutputIndex, CustomizedUVs1Input);
		if (CustomizedUVs2Input != nullptr)
			MatAttr->CustomizedUVs[2].Connect(EditorData->CustomizedUVs[2].OutputIndex, CustomizedUVs2Input);
		if (CustomizedUVs3Input != nullptr)
			MatAttr->CustomizedUVs[3].Connect(EditorData->CustomizedUVs[3].OutputIndex, CustomizedUVs3Input);
		if (CustomizedUVs4Input != nullptr)
			MatAttr->CustomizedUVs[4].Connect(EditorData->CustomizedUVs[4].OutputIndex, CustomizedUVs4Input);
		if (CustomizedUVs5Input != nullptr)
			MatAttr->CustomizedUVs[5].Connect(EditorData->CustomizedUVs[5].OutputIndex, CustomizedUVs5Input);
		if (CustomizedUVs6Input != nullptr)
			MatAttr->CustomizedUVs[6].Connect(EditorData->CustomizedUVs[6].OutputIndex, CustomizedUVs6Input);
		if (CustomizedUVs7Input != nullptr)
			MatAttr->CustomizedUVs[7].Connect(EditorData->CustomizedUVs[7].OutputIndex, CustomizedUVs7Input);
		if (CustomizedUVs8Input != nullptr)
			MatAttr->CustomizedUVs[8].Connect(EditorData->CustomizedUVs[8].OutputIndex, CustomizedUVs8Input);

		// Don't connect WorldDisplacement or TesselationMultiplier in UE5 as they are depricated.
#if ENGINE_MAJOR_VERSION == 4
		if (WorldDisplacementInput != nullptr)
			MatAttr->WorldDisplacement.Connect(UnrealMaterial->GetMaterial()->GetBaseMaterial()->WorldDisplacement.OutputIndex, WorldDisplacementInput);
		if (TMInput != nullptr)
			MatAttr->TessellationMultiplier.Connect(UnrealMaterial->GetMaterial()->GetBaseMaterial()->TessellationMultiplier.OutputIndex, TMInput);
#endif

		MAInput = MatAttr;
		MAInput->MaterialExpressionEditorX = NodePosX + 200;
		MAInput->MaterialExpressionEditorY = NodePosY;
		UnrealMaterial->bUseMaterialAttributes = true;
		NodePosX += 450;
		UnrealMaterial->GetMaterial()->GetBaseMaterial()->EditorX = NodePosX + 200;

	}

	UMaterialExpressionMaterialFunctionCall* MatFunction = NewObject <UMaterialExpressionMaterialFunctionCall>(UnrealMaterial);

#if (ENGINE_MAJOR_VERSION == 4 || (ENGINE_MAJOR_VERSION == 5 && ENGINE_MINOR_VERSION == 0))
	UnrealMaterial->Expressions.Add(MatFunction);
#else		
	UnrealMaterial->GetEditorOnlyData()->ExpressionCollection.Expressions.Add(MatFunction);
#endif

	MatFunction->SetMaterialFunction(MaterialFunction);
	MatFunction->MaterialExpressionEditorX = NodePosX;
	MatFunction->MaterialExpressionEditorY = NodePosY;

	TArray<FFunctionExpressionInput> FuncInputs = MatFunction->FunctionInputs;
	TArray<FFunctionExpressionOutput> FuncOutputs = MatFunction->FunctionOutputs;
	TArray<FFunctionExpressionInput> NewFuncInputs;
	for (FFunctionExpressionInput F : FuncInputs)
	{
		UMaterialExpressionFunctionInput* ExprInput = F.ExpressionInput;
		if (ExprInput != nullptr)
		{
			FName FuncName = ExprInput->InputName;
			if (FuncName == FunctionInputName)
			{
				F.Input.Connect(0, MAInput);
			}
			NewFuncInputs.Add(F);
		}
	}
	MatFunction->FunctionInputs = NewFuncInputs;

#if (ENGINE_MAJOR_VERSION == 4 || (ENGINE_MAJOR_VERSION == 5 && ENGINE_MINOR_VERSION == 0))
	UnrealMaterial->MaterialAttributes.Expression = MatFunction;
#else		
	UnrealMaterial->GetEditorOnlyData()->MaterialAttributes.Expression = MatFunction;
#endif

	UnrealMaterial->PreEditChange(NULL);
	UnrealMaterial->PostEditChange();

	FGlobalComponentReregisterContext RecreateComponents;
#endif
}