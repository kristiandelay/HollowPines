// Copyright Epic Games, Inc. All Rights Reserved.

using UnrealBuildTool;
using System.Collections.Generic;

public class HollowPinesEditorTarget : TargetRules
{
	public HollowPinesEditorTarget(TargetInfo Target) : base(Target)
	{
		DefaultBuildSettings = BuildSettingsVersion.V7;

		Type = TargetType.Editor;
		ExtraModuleNames.AddRange(new string[] { "LyraGame", "LyraEditor" });

		if (!bBuildAllModules)
		{
			NativePointerMemberBehaviorOverride = PointerMemberBehavior.Disallow;
		}

		HollowPinesTarget.ApplySharedLyraTargetSettings(this);

		// This is used for touch screen development along with the "Unreal Remote 2" app
		EnablePlugins.Add("RemoteSession");
	}
}
