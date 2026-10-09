// Copyright Epic Games, Inc. All Rights Reserved.

using UnrealBuildTool;
using System.Collections.Generic;

public class HollowPinesServerSteamTarget : HollowPinesServerTarget
{
	public HollowPinesServerSteamTarget(TargetInfo Target) : base(Target)
	{
		CustomConfig = "Steam";
	}
}
