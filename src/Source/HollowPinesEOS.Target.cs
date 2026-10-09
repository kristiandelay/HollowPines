// Copyright Epic Games, Inc. All Rights Reserved.

using UnrealBuildTool;
using System.Collections.Generic;

public class HollowPinesEOSTarget : HollowPinesTarget
{
	public HollowPinesEOSTarget(TargetInfo Target) : base(Target)
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
