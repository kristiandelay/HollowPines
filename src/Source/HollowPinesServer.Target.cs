// Copyright Epic Games, Inc. All Rights Reserved.

using UnrealBuildTool;
using System.Collections.Generic;

[SupportedPlatforms(UnrealPlatformClass.Server)]
public class HollowPinesServerTarget : TargetRules
{
	public HollowPinesServerTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Server;

		ExtraModuleNames.AddRange(new string[] { "LyraGame" });

		HollowPinesTarget.ApplySharedLyraTargetSettings(this);

		bUseChecksInShipping = true;
	}
}
