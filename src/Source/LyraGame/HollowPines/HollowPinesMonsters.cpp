#include "HollowPinesMonsters.h"
#include "AbilitySystem/LyraAbilitySystemComponent.h"
#include "AbilitySystem/Attributes/LyraHealthSet.h"
#include "Character/LyraHealthComponent.h"
#include "Animation/AnimSequence.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "EngineUtils.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/GameStateBase.h"
#include "Navigation/CrowdFollowingComponent.h"
#include "NavigationSystem.h"
#include "Net/UnrealNetwork.h"

static double MonsterClock(const UWorld* World)
{
    const auto* GS = World->GetGameState();
    return GS ? GS->GetServerWorldTimeSeconds() : World->GetTimeSeconds();
}

void UHollowPinesEncounter::Register(AHollowPinesMonster* Monster) { Monsters.AddUnique(Monster); }
void UHollowPinesEncounter::Remove(AHollowPinesMonster* Monster) { ReleaseTurn(Monster); Monsters.Remove(Monster); }
void UHollowPinesEncounter::ReleaseTurn(AHollowPinesMonster* Monster)
{
    for (auto It = Turns.CreateIterator(); It; ++It)
    {
        if (!It.Key().IsValid()) { It.RemoveCurrent(); continue; }
        auto& Turn = It.Value();
        Turn.Queue.RemoveAll([Monster](const auto& P) { return !P.IsValid() || P.Get() == Monster; });
        if (Turn.Owner.Get() == Monster) Turn.Owner.Reset();
    }
}
AHollowPinesMonster* UHollowPinesEncounter::GetTurnOwner(AActor* Target) const
{
    const auto* Turn = Turns.Find(Target);
    return Turn ? Turn->Owner.Get() : nullptr;
}
bool UHollowPinesEncounter::RequestTurn(AHollowPinesMonster* Monster, AActor* Target)
{
    if (!IsValid(Monster) || !Monster->CanRehearseWith(Target)) return false;
    auto& Turn = Turns.FindOrAdd(Target);
    const double Now = GetWorld()->GetTimeSeconds();
    if (Turn.Owner.IsValid() && (Turn.Owner->bDead || !Turn.Owner->CanRehearseWith(Target) || Now > Turn.Expires)) Turn.Owner.Reset();
    Turn.Queue.RemoveAll([Target](const auto& P) { return !P.IsValid() || P->bDead || !P->CanRehearseWith(Target); });
    if (Turn.Owner.Get() == Monster) return true;
    Turn.Queue.AddUnique(Monster);
    if (!Turn.Owner.IsValid() && Turn.Queue.Num())
    {
        Turn.Owner = Turn.Queue[0]; Turn.Queue.RemoveAt(0);
        Turn.Expires = Now + 9; // Includes approach, animation and recovery; unreachable attackers cannot monopolize a turn.
    }
    return Turn.Owner.Get() == Monster;
}
FVector UHollowPinesEncounter::GetWaitingPosition(AHollowPinesMonster* Monster, AActor* Target) const
{
    TArray<AHollowPinesMonster*> Group;
    float Spacing = 200;
    for (const auto& P : Monsters)
        if (P.IsValid() && !P->bDead && P->GetObservedTarget() == Target)
        { Group.Add(P.Get()); Spacing = FMath::Max(Spacing, P->Profile ? P->Profile->PersonalSpace : 200); }
    Group.Sort([](const auto& A, const auto& B) { return A.GetUniqueID() < B.GetUniqueID(); });
    const int32 Index = FMath::Max(0, Group.IndexOfByKey(Monster));
    const float Radius = FMath::Max(Spacing * 2, Spacing * Group.Num() / (2 * PI) * 1.4f);
    const float Angle = 2 * PI * Index / FMath::Max(1, Group.Num());
    return Target->GetActorLocation() + FVector(FMath::Cos(Angle), FMath::Sin(Angle), 0) * Radius;
}

AHollowPinesMonsterController::AHollowPinesMonsterController(const FObjectInitializer& Initializer)
    : Super(Initializer.SetDefaultSubobjectClass<UCrowdFollowingComponent>(TEXT("PathFollowingComponent")))
{
    if (auto* Crowd = Cast<UCrowdFollowingComponent>(GetPathFollowingComponent()))
    {
        Crowd->SetCrowdSeparation(true);
        Crowd->SetCrowdSeparationWeight(3);
        Crowd->SetCrowdAvoidanceQuality(ECrowdAvoidanceQuality::High);
        Crowd->SetCrowdCollisionQueryRange(1000);
        Crowd->SetCrowdSlowdownAtGoal(true);
        Crowd->SetCrowdAffectFallingVelocity(false);
    }
}
AHollowPinesMonster::AHollowPinesMonster()
{
    PrimaryActorTick.bCanEverTick = true;
    bReplicates = true;
    AIControllerClass = AHollowPinesMonsterController::StaticClass();
    AutoPossessAI = EAutoPossessAI::PlacedInWorldOrSpawned;
    bUseControllerRotationYaw = false;
    GetCharacterMovement()->bOrientRotationToMovement = true;
    GetCharacterMovement()->RotationRate = FRotator(0, 150, 0);
    GetCharacterMovement()->JumpZVelocity = 500;
    GetCharacterMovement()->bUseRVOAvoidance = false;
    GetMesh()->SetCollisionProfileName(TEXT("CharacterMesh"));
    GetMesh()->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
    GetMesh()->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
    AbilitySystem = CreateDefaultSubobject<ULyraAbilitySystemComponent>(TEXT("AbilitySystem"));
    AbilitySystem->SetIsReplicated(true);
    AbilitySystem->SetReplicationMode(EGameplayEffectReplicationMode::Minimal);
    HealthSet = CreateDefaultSubobject<ULyraHealthSet>(TEXT("HealthSet"));
    Health = CreateDefaultSubobject<ULyraHealthComponent>(TEXT("Health"));
}
UAbilitySystemComponent* AHollowPinesMonster::GetAbilitySystemComponent() const { return AbilitySystem; }
void AHollowPinesMonster::OnConstruction(const FTransform& Transform)
{
    Super::OnConstruction(Transform);
    if (!Profile) return;
    GetCapsuleComponent()->SetCapsuleSize(Profile->CapsuleRadius, Profile->CapsuleHalfHeight);
    GetMesh()->SetSkeletalMesh(Profile->Mesh);
    GetMesh()->SetRelativeLocation(FVector(0,0,-Profile->CapsuleHalfHeight));
    // FBX axis conversion makes the imported rigs face +Y. Align to character +X.
    GetMesh()->SetRelativeRotation(FRotator(0,-90,0));
    GetMesh()->SetAnimInstanceClass(Profile->AnimationClass);
    GetCharacterMovement()->MaxWalkSpeed = Profile->WalkSpeed;
}
void AHollowPinesMonster::BeginPlay()
{
    Super::BeginPlay();
    HomeTransform = GetActorTransform();
    AbilitySystem->InitAbilityActorInfo(this, this);
    Health->InitializeWithAbilitySystem(AbilitySystem);
    Health->OnHealthChanged.AddDynamic(this, &ThisClass::OnHealthChanged);
    if (HasAuthority()) GetWorld()->GetSubsystem<UHollowPinesEncounter>()->Register(this);
}
void AHollowPinesMonster::EndPlay(const EEndPlayReason::Type Reason)
{
    if (auto* Director = GetWorld()->GetSubsystem<UHollowPinesEncounter>()) Director->Remove(this);
    Health->UninitializeFromAbilitySystem();
    Super::EndPlay(Reason);
}
void AHollowPinesMonster::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AHollowPinesMonster, ActionState);
    DOREPLIFETIME(AHollowPinesMonster, bDead);
    DOREPLIFETIME(AHollowPinesMonster, bPaused);
}
float AHollowPinesMonster::GetActionAge() const { return FMath::Max(0., MonsterClock(GetWorld()) - ActionState.ServerStartTime); }
UAnimSequence* AHollowPinesMonster::GetActionSequence() const
{
    if (Profile) if (const auto* Clip = Profile->Actions.Find(ActionState.Action)) return *Clip;
    return nullptr;
}
bool AHollowPinesMonster::CanRehearseWith(AActor* Target) const
{
    return bRehearseAttacks && !bDead && !bPaused && IsValid(Target) && Target == PracticeTarget && !Target->IsA<APawn>();
}
void AHollowPinesMonster::SetAction(EHPMonsterAction Action)
{
    if (!HasAuthority()) return;
    ActionState.Action = Action; ActionState.ServerStartTime = MonsterClock(GetWorld()); ++ActionState.Revision;
    OnRep_Action(); ForceNetUpdate();
}
void AHollowPinesMonster::OnRep_Action()
{
    if (ActionState.Action == EHPMonsterAction::Death)
    {
        bDead = true;
        GetCharacterMovement()->DisableMovement();
        GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        GetMesh()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    }
}
void AHollowPinesMonster::SetPaused(bool bPause)
{
    if (!HasAuthority()) return;
    bPaused = bPause;
    if (bPause)
    {
        if (auto* AI = Cast<AAIController>(GetController())) AI->StopMovement();
        GetWorld()->GetSubsystem<UHollowPinesEncounter>()->ReleaseTurn(this);
    }
}
void AHollowPinesMonster::PreviewAction(EHPMonsterAction Action)
{
    if (!HasAuthority() || bDead || Action == EHPMonsterAction::None || !Profile || !Profile->Actions.Contains(Action)) return;
    if (auto* AI = Cast<AAIController>(GetController())) AI->StopMovement();
    if (Action >= EHPMonsterAction::HitFront) GetWorld()->GetSubsystem<UHollowPinesEncounter>()->ReleaseTurn(this);
    if (Action == EHPMonsterAction::Death) { bDead = true; Health->StartDeath(); }
    SetAction(Action);
}
void AHollowPinesMonster::OnHealthChanged(ULyraHealthComponent*, float Old, float New, AActor* InstigatorActor)
{
    if (!HasAuthority() || bDead || New >= Old) return;
    EHPMonsterAction Hit = EHPMonsterAction::HitFront;
    if (InstigatorActor)
    {
        const float Side = FVector::DotProduct(GetActorRightVector(), (InstigatorActor->GetActorLocation()-GetActorLocation()).GetSafeNormal());
        if (FMath::Abs(Side) > .4f) Hit = Side < 0 ? EHPMonsterAction::HitLeft : EHPMonsterAction::HitRight;
    }
    PreviewAction(New <= 0 ? EHPMonsterAction::Death : Hit);
}
void AHollowPinesMonster::Landed(const FHitResult& Hit)
{
    Super::Landed(Hit);
    if (HasAuthority() && !bDead && ActionState.Action == EHPMonsterAction::JumpLoop) SetAction(EHPMonsterAction::Land);
}
void AHollowPinesMonster::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (!HasAuthority() || !Profile) return;
    const auto* Clip = GetActionSequence();
    if (bDead)
    {
        if (Clip && GetActionAge() >= Clip->GetPlayLength() && Health->GetDeathState() == ELyraDeathState::DeathStarted) Health->FinishDeath();
        return;
    }
    if (IsActing())
    {
        if (ActionState.Action == EHPMonsterAction::JumpLoop) return;
        if (Clip && GetActionAge() < Clip->GetPlayLength()) return;
        if (ActionState.Action == EHPMonsterAction::JumpStart)
        {
            LaunchCharacter(FVector(0,0,GetCharacterMovement()->JumpZVelocity), false, true);
            SetAction(EHPMonsterAction::JumpLoop); return;
        }
        GetWorld()->GetSubsystem<UHollowPinesEncounter>()->ReleaseTurn(this);
        NextTurn = GetWorld()->GetTimeSeconds() + 1.2;
        SetAction(EHPMonsterAction::None);
    }
    if (GetWorld()->GetTimeSeconds() >= NextThink)
    {
        NextThink = GetWorld()->GetTimeSeconds()+.3;
        Think();
    }
}
void AHollowPinesMonster::Think()
{
    auto* AI = Cast<AAIController>(GetController());
    if (!AI || bPaused) return;
    auto* Nav = FNavigationSystem::GetCurrent<UNavigationSystemV1>(GetWorld());
    auto* Director = GetWorld()->GetSubsystem<UHollowPinesEncounter>();
    AActor* Target = CanRehearseWith(PracticeTarget) ? PracticeTarget.Get() : nullptr;
    float Nearest = FMath::Square(AwarenessRadius);
    if (!Target)
        for (FConstPlayerControllerIterator It=GetWorld()->GetPlayerControllerIterator(); It; ++It)
            if (const auto* PC = It->Get())
                if (APawn* Pawn = PC->GetPawn())
                {
                    const auto* HP = ULyraHealthComponent::FindHealthComponent(Pawn);
                    const float Distance = FVector::DistSquared(Pawn->GetActorLocation(),GetActorLocation());
                    if ((!HP || !HP->IsDeadOrDying()) && Distance < Nearest && AI->LineOfSightTo(Pawn)) { Target=Pawn; Nearest=Distance; }
                }
    if (ObservedTarget.Get() != Target) { Director->ReleaseTurn(this); ObservedTarget=Target; }
    if (Target)
    {
        FVector Goal = Director->GetWaitingPosition(this,Target);
        if (CanRehearseWith(Target) && GetWorld()->GetTimeSeconds() >= NextTurn && Director->RequestTurn(this,Target))
        {
            const FVector Away = (GetActorLocation()-Target->GetActorLocation()).GetSafeNormal2D();
            Goal = Target->GetActorLocation()+Away*Profile->MeleeReach*.65;
            if (FVector::Dist2D(GetActorLocation(),Target->GetActorLocation()) < Profile->MeleeReach)
            {
                AI->StopMovement();
                SetActorRotation(FRotator(0,(Target->GetActorLocation()-GetActorLocation()).Rotation().Yaw,0));
                PreviewAction(static_cast<EHPMonsterAction>(static_cast<uint8>(EHPMonsterAction::Attack1)+(AttackIndex++%3)));
                return;
            }
        }
        FNavLocation Projected;
        GetCharacterMovement()->MaxWalkSpeed = FVector::DistSquared2D(GetActorLocation(),Goal)>FMath::Square(900.f) ? Profile->RunSpeed : Profile->WalkSpeed;
        if (Nav && Nav->ProjectPointToNavigation(Goal,Projected,FVector(150,150,800)))
            if (FVector::DistSquared2D(GetActorLocation(),Projected.Location)>FMath::Square(40.f)) AI->MoveToLocation(Projected.Location,25,false);
        if (AI->GetMoveStatus()==EPathFollowingStatus::Idle) AI->SetFocus(Target);
        else AI->ClearFocus(EAIFocusPriority::Gameplay);
    }
    else if (bPatrol && Nav && GetWorld()->GetTimeSeconds() >= NextPatrol)
    {
        GetCharacterMovement()->MaxWalkSpeed = Profile->WalkSpeed;
        FNavLocation Goal;
        if (Nav->GetRandomReachablePointInRadius(HomeTransform.GetLocation(),PatrolRadius,Goal)) AI->MoveToLocation(Goal.Location,80,false);
        NextPatrol=GetWorld()->GetTimeSeconds()+6;
        AI->ClearFocus(EAIFocusPriority::Gameplay);
    }
}
void UHollowPinesMonsterAnimInstance::NativeUpdateAnimation(float DeltaSeconds)
{
    Super::NativeUpdateAnimation(DeltaSeconds);
    const auto* Monster = Cast<AHollowPinesMonster>(TryGetPawnOwner());
    if (!Monster) return;
    Speed = Monster->GetVelocity().Size2D();
    if (auto* Clip = Monster->GetActionSequence())
    {
        ActionSequence = Clip;
        const float Length = FMath::Max(.01f,Clip->GetPlayLength());
        ActionTime = Monster->ActionState.Action == EHPMonsterAction::JumpLoop ? FMath::Fmod(Monster->GetActionAge(),Length) : FMath::Min(Monster->GetActionAge(),Length);
    }
    ActionWeight = FMath::FInterpConstantTo(ActionWeight,Monster->IsActing()?1.f:0.f,DeltaSeconds,8.f);
}

AHollowPinesMonsterReviewGameMode::AHollowPinesMonsterReviewGameMode()
{
    PlayerControllerClass=AHollowPinesMonsterReviewController::StaticClass();
    HUDClass=AHollowPinesMonsterReviewHUD::StaticClass();
}
void AHollowPinesMonsterReviewController::SetupInputComponent()
{
    Super::SetupInputComponent();
    InputComponent->BindKey(EKeys::F1,IE_Pressed,this,&ThisClass::SelectNext);
    InputComponent->BindKey(EKeys::F2,IE_Pressed,this,&ThisClass::PausePreview);
    InputComponent->BindKey(EKeys::F3,IE_Pressed,this,&ThisClass::RehearsePreview);
    InputComponent->BindKey(EKeys::One,IE_Pressed,this,&ThisClass::AttackOne);
    InputComponent->BindKey(EKeys::Two,IE_Pressed,this,&ThisClass::AttackTwo);
    InputComponent->BindKey(EKeys::Three,IE_Pressed,this,&ThisClass::AttackThree);
    InputComponent->BindKey(EKeys::J,IE_Pressed,this,&ThisClass::JumpPreview);
    InputComponent->BindKey(EKeys::H,IE_Pressed,this,&ThisClass::HitPreview);
    InputComponent->BindKey(EKeys::X,IE_Pressed,this,&ThisClass::DeathPreview);
    InputComponent->BindKey(EKeys::BackSpace,IE_Pressed,this,&ThisClass::ResetPreview);
}
void AHollowPinesMonsterReviewController::SelectNext()
{
    TArray<AHollowPinesMonster*> Monsters;
    for (TActorIterator<AHollowPinesMonster> It(GetWorld());It;++It) Monsters.Add(*It);
    Monsters.Sort([](const auto& A,const auto& B){return A.GetName()<B.GetName();});
    if (Monsters.Num()) SelectedMonster=Monsters[(Monsters.IndexOfByKey(SelectedMonster)+1)%Monsters.Num()];
}
void AHollowPinesMonsterReviewController::AttackOne(){ServerReview(SelectedMonster,static_cast<int32>(EHPMonsterAction::Attack1));}
void AHollowPinesMonsterReviewController::AttackTwo(){ServerReview(SelectedMonster,static_cast<int32>(EHPMonsterAction::Attack2));}
void AHollowPinesMonsterReviewController::AttackThree(){ServerReview(SelectedMonster,static_cast<int32>(EHPMonsterAction::Attack3));}
void AHollowPinesMonsterReviewController::JumpPreview(){ServerReview(SelectedMonster,static_cast<int32>(EHPMonsterAction::JumpStart));}
void AHollowPinesMonsterReviewController::HitPreview(){ServerReview(SelectedMonster,static_cast<int32>(EHPMonsterAction::HitFront)+(HitIndex++%3));}
void AHollowPinesMonsterReviewController::DeathPreview(){ServerReview(SelectedMonster,static_cast<int32>(EHPMonsterAction::Death));}
void AHollowPinesMonsterReviewController::ResetPreview(){ServerReview(SelectedMonster,100);}
void AHollowPinesMonsterReviewController::PausePreview(){ServerReview(SelectedMonster,101);}
void AHollowPinesMonsterReviewController::RehearsePreview(){ServerReview(SelectedMonster,102);}
void AHollowPinesMonsterReviewController::ClientSelect_Implementation(AHollowPinesMonster* Monster){SelectedMonster=Monster;}
void AHollowPinesMonsterReviewController::ServerReview_Implementation(AHollowPinesMonster* Monster,int32 Command)
{
    if (!IsValid(Monster) || Monster->GetWorld()!=GetWorld() || !GetPawn() || FVector::DistSquared(Monster->GetActorLocation(),GetPawn()->GetActorLocation())>FMath::Square(30000.f)) return;
    if (Command==100)
    {
        const auto Class=Monster->GetClass(); const auto Transform=Monster->HomeTransform;
        AActor* PracticeTarget=Monster->PracticeTarget;
        const float PatrolRadius=Monster->PatrolRadius, AwarenessRadius=Monster->AwarenessRadius;
        Monster->Destroy();
        FActorSpawnParameters Params;Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;
        auto* Replacement=GetWorld()->SpawnActor<AHollowPinesMonster>(Class,Transform,Params);
        if (Replacement)
        {
            Replacement->PracticeTarget=PracticeTarget;
            Replacement->PatrolRadius=PatrolRadius;Replacement->AwarenessRadius=AwarenessRadius;
        }
        ClientSelect(Replacement);
    }
    else if (Command==101) Monster->SetPaused(!Monster->bPaused);
    else if (Command==102)
    {
        const bool Enable=!Monster->bRehearseAttacks;
        for (TActorIterator<AHollowPinesMonster> It(GetWorld());It;++It)
        { It->bRehearseAttacks=Enable; if (!Enable) GetWorld()->GetSubsystem<UHollowPinesEncounter>()->ReleaseTurn(*It); }
    }
    else if (Command>0 && Command<=static_cast<int32>(EHPMonsterAction::Death)) Monster->PreviewAction(static_cast<EHPMonsterAction>(Command));
}
void AHollowPinesMonsterReviewHUD::DrawHUD()
{
    Super::DrawHUD();
    const auto* PC=Cast<AHollowPinesMonsterReviewController>(GetOwningPlayerController());
    if (!Canvas || !PC) return;
    DrawRect(FLinearColor(0,0,0,.65f),22,110,620,86);
    const FString Name=IsValid(PC->SelectedMonster)?PC->SelectedMonster->GetName():TEXT("Press F1 to select a creature");
    DrawText(TEXT("MONSTER MOTION REVIEW | ")+Name,FLinearColor::White,34,119,GEngine->GetSmallFont());
    DrawText(TEXT("F1 Select   F2 Pause AI   1/2/3 Attacks   J Jump   H Hit   X Death   Backspace Reset"),FLinearColor::White,34,143,GEngine->GetSmallFont());
    DrawText(TEXT("F3 Dummy turn rehearsal | Attacks on players disabled"),FLinearColor(.65f,.85f,.72f),34,168,GEngine->GetSmallFont());
}
