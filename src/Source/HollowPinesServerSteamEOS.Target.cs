// Copyright Epic Games, Inc. All Rights Reserved.

using UnrealBuildTool;
using System.Collections.Generic;

public class HollowPinesServerSteamEOSTarget : HollowPinesServerTarget
{
	public HollowPinesServerSteamEOSTarget(TargetInfo Target) : base(Target)
	{
		CustomConfig = "SteamEOS";

		EnablePlugins.AddRange(
			new string[]
			{
				"OnlineServicesEOS",
				"OnlineSubsystemEOS"
			}
		);

		OptionalPlugins.Add("EOSReservedHooks");
	}
}
