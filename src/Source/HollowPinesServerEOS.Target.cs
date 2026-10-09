// Copyright Epic Games, Inc. All Rights Reserved.

using UnrealBuildTool;
using System.Collections.Generic;

public class HollowPinesServerEOSTarget : HollowPinesServerTarget
{
	public HollowPinesServerEOSTarget(TargetInfo Target) : base(Target)
	{
		CustomConfig = "EOS";

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
