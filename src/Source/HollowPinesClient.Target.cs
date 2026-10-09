// Copyright Epic Games, Inc. All Rights Reserved.

using UnrealBuildTool;
using System.Collections.Generic;

public class HollowPinesClientTarget : TargetRules
{
	public HollowPinesClientTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Client;

		ExtraModuleNames.AddRange(new string[] { "LyraGame" });

		HollowPinesTarget.ApplySharedLyraTargetSettings(this);
	}
}
