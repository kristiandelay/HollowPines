// EasySkyV2, Copyright 2021 PS Studios

#pragma once

#include "CoreMinimal.h"
#include "Modules/ModuleManager.h"

class FEasySkyV2Module : public IModuleInterface
{
public:

	/** IModuleInterface implementation */
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;
};
