// EasySkyV2, Copyright 2021 PS Studios

#include "EasySkyV2.h"
#include "Interfaces/IPluginManager.h"
#include "ShaderCore.h"
#include "Misc/Paths.h"

#define LOCTEXT_NAMESPACE "FEasySkyV2Module"

void FEasySkyV2Module::StartupModule()
{
	FString PluginName = "EasySkyV2";
	FString Content = IPluginManager::Get().FindPlugin("EasySkyV2")->GetContentDir();
	FString ShaderDir = FPaths::Combine(Content, TEXT("Shaders"));

	/*
	FString Content;
	FString ShaderDir;
#if (ENGINE_MAJOR_VERSION == 4 || ENGINE_MAJOR_VERSION == 5 && ENGINE_MINOR_VERSION < 2)
	{
		FString Content = IPluginManager::Get().FindPlugin("EasySkyV2")->GetContentDir();
		FString ShaderDir = FPaths::Combine(Content, TEXT("Shaders"));
	}
#else
	{
		Content = IPluginManager::Get().FindPlugin("EasySkyV2")->GetContentDir();
		ShaderDir = FPaths::Combine(Content, TEXT("Shaders"));
	}
#endif
	*/
	AddShaderSourceDirectoryMapping("/Plugin/Shaders", ShaderDir);
}

void FEasySkyV2Module::ShutdownModule()
{
	// This function may be called during shutdown to clean up your module.  For modules that support dynamic reloading,
	// we call this function before unloading the module.
}

#undef LOCTEXT_NAMESPACE
	
IMPLEMENT_MODULE(FEasySkyV2Module, EasySkyV2)