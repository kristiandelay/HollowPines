// Copyright Epic Games, Inc. All Rights Reserved.

using UnrealBuildTool;
using System.Collections.Generic;

// SteamEOS refers to a game published and launched on Steam while still taking advantage of EOS for online and crossplay (integrated platform).

public class HollowPinesSteamEOSTarget : HollowPinesTarget
{
	public HollowPinesSteamEOSTarget(TargetInfo Target) : base(Target)
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
