// Copyright Epic Games, Inc. All Rights Reserved.

using UnrealBuildTool;
using System.Collections.Generic;

public class HollowPinesSteamTarget : HollowPinesTarget
{
	public HollowPinesSteamTarget(TargetInfo Target) : base(Target)
	{
		CustomConfig = "Steam";
	}
}
