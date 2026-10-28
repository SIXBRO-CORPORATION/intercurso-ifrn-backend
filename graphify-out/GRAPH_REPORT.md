# Graph Report - intercurso-ifrn-backend  (2026-10-28)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 3467 nodes · 16767 edges · 264 communities (97 shown, 167 thin omitted)
- Extraction: 80% EXTRACTED · 20% INFERRED · 0% AMBIGUOUS · INFERRED: 3289 edges (avg confidence: 0.93)
- Token cost: 12,052 input · 3,120 output

## Graph Freshness
- Built from commit: `c250073d`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Bracket Management Adapters
- Test Mocks and Stubs
- Match Control Ports
- Season and Team Adapters
- Database Migrations
- User Profile Management
- Database Session Dependencies
- Bracket Configuration Logic
- Bracket Statistics and Status
- Team Member Donations
- Match Search and Discovery
- Modality Management
- Development Docker Configuration
- Season Validation Tests
- Production Docker Configuration
- Match Response Mapping
- Domain Validation Rules
- Real-time Event Broadcaster
- Team Response Mapping
- Season Repository Access
- Authentication and OAuth Ports
- Team Repository Access
- Refresh Token Management
- Knockout Stage Drawing
- Match Metadata Enums
- Bracket Group Persistence
- Bracket Operation Ports
- Generic Context Operations
- Bracket Model Mapping
- Push Notification Service
- Live Ticket Management
- Match Event Persistence
- Modality Repository Access
- Schema Migration History
- Docker Compose Services
- Database Environment Config
- IP Rate Limiting
- Season Notification Content
- Penalty Shootout Tests
- Team Creation Tests
- Device Token Management
- Team Status Management
- Test Data Seeding
- Security and JWT Config
- Modality Creation Tests
- Notification API Endpoints
- User Repository Access
- Development Deployment Workflow
- Production Deployment Workflow
- CI Pull Request Verification
- Audit Log Persistence
- Integration Test Fakes
- Tournament Draw Engine
- Group Standings Resolver
- Knockout Draw Tests
- Bracket Repository Access
- JWT Authentication Utilities
- Match Event Endpoints
- Bracket Group Repository
- Season Modality Persistence
- Live Ticket Adapters
- Auth Callback Tests
- SUAP OAuth Integration
- Device Token Registration
- Personal Notification Tests
- Match Event Publisher Tests
- Bracket Creation Tests
- Team Listing Tests
- Modality Model Mapping
- Volleyball Configuration Persistence
- Team Approval Tests
- Team Details Tests
- R2 Storage Integration
- Scheduled Season Jobs
- App Lifecycle and Scheduler
- Active Season Retrieval
- Modality Configuration Persistence
- Team Invite Tests
- Team Submission Tests
- Round Information Logic
- Season Management Tests
- Match Broadcast Content
- Season Finish Tests
- Registration Reopening Tests
- Donation Confirmation Tests
- Project Documentation ADRs
- Device Token Removal
- Modality Activation Tests
- Submission Eligibility Logic
- JWT Provider Tests
- Match Start Tests
- Season Details Tests
- Member Removal Tests
- Leave Team Tests
- Member Exit Tests
- Public Match Adapter Tests
- Season Creation API Tests
- Close Registration Adapter Tests
- Token Refresh Security Tests
- Season Broadcast Port
- Bracket Listing Adapter Tests
- Bracket Resorting Adapter Tests
- Read Repository Port
- Live Server Test Fixture
- Bracket Details Adapter Tests
- Season Listing Adapter Tests
- Match Deletion Adapter Tests
- User Creation Request Validation
- Write Repository Port
- Season and Match Documentation
- Bracket Configuration Suggestion Tests
- Bracket Creation Request Validation
- Device Token Registration Request
- Season Date Edit Validation
- Match Update Request Validation
- Match Goal Request Model
- Token Refresh Response Model
- Real-time Access Documentation
- Match Configuration ADRs
- Team Submission Use Cases
- Role Based Access Control
- Season Finalization Use Case
- Modality Registration Use Case
- Team Creation Use Case
- Invitation Entry Use Case
- Member Management Use Case
- Backend Project Root
- Backend Project Metadata

## God Nodes (most connected - your core abstractions)
1. `Context` - 425 edges
2. `BusinessException` - 314 edges
3. `Team` - 251 edges
4. `Match` - 250 edges
5. `User` - 228 edges
6. `TeamRepositoryPort` - 187 edges
7. `Season` - 181 edges
8. `AuditLogger` - 177 edges
9. `UserRepositoryPort` - 159 edges
10. `MatchRepositoryPort` - 149 edges

## Surprising Connections (you probably didn't know these)
- `test_accepts_fields_and_photo_in_one_request()` --uses--> `Team`  [INFERRED]
  tests/integration/test_create_team_multipart.py → domain/team/team.py
- `CreateBracketAdapter` --uses--> `Context`  [INFERRED]
  business/bracket/create_bracket_adapter.py → core/context.py
- `CreateBracketAdapter` --uses--> `SeasonModalityRepositoryPort`  [INFERRED]
  business/bracket/create_bracket_adapter.py → core/persistence/season/season_modality_repository_port.py
- `CreateBracketAdapter` --uses--> `SeasonRepositoryPort`  [INFERRED]
  business/bracket/create_bracket_adapter.py → core/persistence/season/season_repository_port.py
- `CreateBracketAdapter` --uses--> `Bracket`  [INFERRED]
  business/bracket/create_bracket_adapter.py → domain/bracket/bracket.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Fluxo de Gestão de Partidas** — docs_spec_uc013_gestaodepartidas_iniciarpartida_iniciar_partida, docs_spec_uc014_gestaodepartidas_registrarevento_registrar_evento, docs_spec_uc015_gestaodepartidas_finalizarpartida_finalizar_partida, docs_spec_uc017_gestaodepartidas_corrigirevento_corrigir_evento [EXTRACTED 0.90]
- **Season Lifecycle Management** — docs_spec_uc001, docs_spec_uc002, docs_spec_uc003 [EXTRACTED 1.00]
- **Team Registration Flow** — docs_spec_uc005, docs_spec_uc006, docs_spec_uc008, docs_spec_uc009 [EXTRACTED 1.00]
- **Ciclo de Vida do Chaveamento** — docs_spec_uc011_gestaodechaveamento_criarchaveamento_criar_chaveamento, docs_spec_uc012_gestaodechaveamento_gerenciarchaveamento_gerenciar_chaveamento, docs_spec_uc015_gestaodepartidas_finalizarpartida_finalizar_partida [INFERRED 0.80]
- **Real-time Communication Stack** — docs_adr_adr001, docs_adr_adr003, docs_adr_adr005 [INFERRED 0.90]

## Communities (264 total, 167 thin omitted)

### Community 0 - "Bracket Management Adapters"
Cohesion: 0.05
Nodes (93): CreateBracketAdapter, DeleteMatchAdapter, GetBracketDetailsAdapter, ListBracketMatchesAdapter, ListBracketsBySeasonAdapter, ResortBracketAdapter, UpdateMatchAdapter, apply_event_correction() (+85 more)

### Community 1 - "Test Mocks and Stubs"
Cohesion: 0.07
Nodes (40): TeamMemberRole, make_adapter(), make_in_progress_match(), make_mocks(), stub_empty_management_context(), make_context(), TestPauseClockAdapter, TestResumeClockAdapter (+32 more)

### Community 2 - "Match Control Ports"
Cohesion: 0.06
Nodes (59): DeleteEventPort, EndPenaltyShootoutPort, EndPeriodPort, EndSetPort, FinishMatchPort, PauseClockPort, RegisterCardPort, RegisterGoalPort (+51 more)

### Community 3 - "Season and Team Adapters"
Cohesion: 0.06
Nodes (49): GetBracketConfigSuggestionAdapter, CloseRegistrationAdapter, CreateSeasonAdapter, GetSeasonDetailsAdapter, ListSeasonsAdapter, ManageSeasonAdapter, ReopenRegistrationAdapter, CreateTeamAdapter (+41 more)

### Community 4 - "Database Migrations"
Cohesion: 0.04
Nodes (25): run_migrations_offline(), run_migrations_online(), upgrade(), upgrade(), upgrade(), downgrade(), upgrade(), upgrade() (+17 more)

### Community 5 - "User Profile Management"
Cohesion: 0.08
Nodes (24): CreateUserAdapter, GetUserProfileAdapter, CreateUserByAdminPort, CreateUserPort, GetUserProfilePort, UpdateUserByAdminPort, _to_int(), User (+16 more)

### Community 6 - "Database Session Dependencies"
Cohesion: 0.26
Nodes (43): get_db(), get_match_state(), get_bracket_details_port(), get_create_bracket_port(), get_delete_match_port(), get_draw_knockout_stage_port(), get_list_bracket_matches_port(), get_list_brackets_by_season_port() (+35 more)

### Community 7 - "Bracket Configuration Logic"
Cohesion: 0.08
Nodes (15): _distribute_evenly(), resolve_configuration(), suggest_configuration(), _suggest_group_stage_knockout(), validate_team_count_for_format(), build_draw(), make_team_ids(), TestGroupStageKnockoutDraw (+7 more)

### Community 8 - "Bracket Statistics and Status"
Cohesion: 0.10
Nodes (17): next_power_of_two(), estimate_match_counts(), _knockout_rounds(), build_bracket_stats(), _can_draw_knockout_stage(), load_team_names(), BracketStatus, ModalityFormat (+9 more)

### Community 9 - "Team Member Donations"
Cohesion: 0.11
Nodes (15): DonationStatus, TeamMember, TeamMemberRepositoryAdapter, TeamMemberMapper, TeamEntity, TeamMemberEntity, TestTeamMemberQueries, member() (+7 more)

### Community 10 - "Match Search and Discovery"
Cohesion: 0.11
Nodes (7): advance_semifinal_loser(), ListPublicMatchesPort, Match, MatchRepositoryAdapter, MatchMapper, TestMatchQueries, TestSearchBySeason

### Community 11 - "Modality Management"
Cohesion: 0.12
Nodes (19): CreateModalityAdapter, ListAllModalitiesAdapter, ListModalitiesAdapter, attach_configurations(), CreateModalityPort, ListAllModalitiesPort, ListModalitiesPort, UpdateModalityActivePort (+11 more)

### Community 12 - "Development Docker Configuration"
Cohesion: 0.05
Nodes (44): build, container_name, depends_on, env_file, networks, ports, restart, postgres (+36 more)

### Community 13 - "Season Validation Tests"
Cohesion: 0.10
Nodes (14): ConflictException, arrange_valid_flow(), make_adapter(), make_context(), TestCreateSeasonAdapter, TestCreateSeasonRulesDocument, register_exception_handler(), business_exception_handler() (+6 more)

### Community 14 - "Production Docker Configuration"
Cohesion: 0.05
Nodes (41): build, cap_drop, condition, depends_on, env_file, expose, healthcheck, image (+33 more)

### Community 15 - "Match Response Mapping"
Cohesion: 0.13
Nodes (17): TestMatchTeamPhotoUrl, MatchModelMapper, team(), MatchListItemResponse, MatchListResponse, MatchCardSummaryResponse, MatchManagementResponse, MatchModalityConfigurationResponse (+9 more)

### Community 16 - "Domain Validation Rules"
Cohesion: 0.13
Nodes (13): evaluate_approve_eligibility(), _gender_quota_block_reason(), AbstractDomain, ModalityGenderMode, ScoreType, make_adapter(), test_list_all_modalities_attaches_volleyball_configuration_for_sets_modality(), test_list_all_modalities_returns_active_and_inactive() (+5 more)

### Community 17 - "Real-time Event Broadcaster"
Cohesion: 0.13
Nodes (9): Broadcaster, ConnectionLimitExceededError, RealtimeEvent, format_sse_message(), stream_channel(), TestBroadcaster, _FakeRequest, _parse() (+1 more)

### Community 18 - "Team Response Mapping"
Cohesion: 0.11
Nodes (10): _modality_limits(), TeamModelMapper, TeamDetailsResponse, TeamInvitePreviewResponse, TeamJoinResponse, TeamMemberResponse, TeamNextMatchResponse, TeamNextMatchTeamResponse (+2 more)

### Community 19 - "Season Repository Access"
Cohesion: 0.14
Nodes (10): Season, SeasonRepositoryAdapter, SeasonMapper, SeasonEntity, _build_season_broadcast(), _notify_after_commit(), run_close_seasons_job(), TestSeasonSchedulerQueries (+2 more)

### Community 20 - "Authentication and OAuth Ports"
Cohesion: 0.16
Nodes (15): LoginWithSuapPort, LogoutPort, OAuthProviderPort, RefreshAccessTokenPort, AuthToken, SUAPUserData, _clean_numeric_string(), LoginWithSuapAdapter (+7 more)

### Community 21 - "Team Repository Access"
Cohesion: 0.14
Nodes (5): Team, TeamRepositoryAdapter, TeamMapper, make_team(), TestTeamQueries

### Community 22 - "Refresh Token Management"
Cohesion: 0.13
Nodes (6): RefreshTokenRepositoryPort, RefreshToken, RefreshTokenRepositoryAdapter, RefreshTokenMapper, RefreshTokenEntity, get_refresh_token_repository()

### Community 23 - "Knockout Stage Drawing"
Cohesion: 0.13
Nodes (15): DrawKnockoutStageAdapter, classified_teams_by_group(), draw_knockout_pairs(), _draw_pairs_without_constraint(), find_first_round_knockout_slots(), group_stage_pending_matches(), knockout_stage_already_drawn(), _try_draw_pairs() (+7 more)

### Community 24 - "Match Metadata Enums"
Cohesion: 0.22
Nodes (8): BracketGroupTeam, MatchCategory, MatchStatus, MatchType, MatchPlan, _override_complete_match_state(), build_scenario(), TestListBracketMatchesAdapter

### Community 25 - "Bracket Group Persistence"
Cohesion: 0.13
Nodes (10): BracketGroupTeamRepositoryAdapter, BracketGroupTeamMapper, BracketGroupTeamEntity, _jsonb_sqlite(), session_and_statements(), _compile_jsonb_for_sqlite(), make_match(), session() (+2 more)

### Community 26 - "Bracket Operation Ports"
Cohesion: 0.14
Nodes (19): CreateBracketPort, DeleteMatchPort, DrawKnockoutStagePort, GetBracketConfigSuggestionPort, GetBracketDetailsPort, ListBracketMatchesPort, ListBracketsBySeasonPort, ResortBracketPort (+11 more)

### Community 28 - "Bracket Model Mapping"
Cohesion: 0.13
Nodes (9): BracketModelMapper, BracketConfigSuggestionResponse, BracketDetailResponse, BracketGroupResponse, BracketGroupTeamResponse, BracketMatchResponse, BracketResponse, BracketSummaryResponse (+1 more)

### Community 29 - "Push Notification Service"
Cohesion: 0.09
Nodes (6): PushSenderPort, _build_credential(), _get_firebase_app(), MessagingSettings, PersonalNotifier, TestFCMCredentialBuilding

### Community 30 - "Live Ticket Management"
Cohesion: 0.11
Nodes (7): LiveTicketPort, _connection_key(), list_matches(), stream_match_events(), stream_season_events(), get_broadcaster(), get_live_ticket_port()

### Community 31 - "Match Event Persistence"
Cohesion: 0.16
Nodes (6): MatchEventRepositoryAdapter, MatchEventMapper, MatchEventEntity, add(), make_event(), TestMatchEventQueries

### Community 32 - "Modality Repository Access"
Cohesion: 0.15
Nodes (10): ModalityRepositoryAdapter, ModalityMapper, ModalityEntity, SeasonModalityEntity, bracket(), _jsonb_for_sqlite(), match(), session() (+2 more)

### Community 33 - "Schema Migration History"
Cohesion: 0.12
Nodes (8): upgrade(), upgrade(), BracketMapper, MatchSetMapper, BracketEntity, MatchSetEntity, TestMatchSetQueries, match_set()

### Community 34 - "Docker Compose Services"
Cohesion: 0.06
Nodes (31): build, depends_on, env_file, image, ports, volumes, context, dockerfile (+23 more)

### Community 35 - "Database Environment Config"
Cohesion: 0.06
Nodes (31): postgres, DATABASE_URL, DATABASE_URL_SYNC, POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER, SEED_ADMIN_MATRICULA, interval (+23 more)

### Community 36 - "IP Rate Limiting"
Cohesion: 0.12
Nodes (8): get_anonymous_ticket_rate_limiter_singleton(), IpRateLimiter, TestIpRateLimiter, get_anonymous_ticket_rate_limiter(), issue_live_ticket(), LiveChannelType, LiveTicketRequest, LiveTicketResponse

### Community 37 - "Season Notification Content"
Cohesion: 0.14
Nodes (10): _format_date(), registration_closed_content(), registration_opened_content(), registration_reopened_content(), season_finished_content(), SeasonBroadcastNotifier, _drain(), make_notifier() (+2 more)

### Community 38 - "Penalty Shootout Tests"
Cohesion: 0.20
Nodes (12): PenaltyKickResult, make_context(), make_end_adapter(), make_match(), make_mocks(), make_register_kick_adapter(), make_start_adapter(), TestEndPenaltyShootoutAdapter (+4 more)

### Community 39 - "Team Creation Tests"
Cohesion: 0.19
Nodes (6): arrange_valid_flow(), make_adapter(), make_context(), make_open_season(), TestCreateTeamAdapter, TestCreateTeamPhoto

### Community 40 - "Device Token Management"
Cohesion: 0.16
Nodes (5): DeviceTokenRepositoryPort, DeviceToken, DeviceTokenRepositoryAdapter, DeviceTokenMapper, DeviceTokenEntity

### Community 41 - "Team Status Management"
Cohesion: 0.16
Nodes (9): DeleteTeamAdapter, RegenerateInviteAdapter, RejectTeamAdapter, ReturnTeamToDraftAdapter, make_context(), TestDeleteTeamAdapter, TestRegenerateInviteAdapter, TestRejectTeamAdapter (+1 more)

### Community 43 - "Test Data Seeding"
Cohesion: 0.20
Nodes (20): close_db(), MatchEntity, UserEntity, apply_result(), BracketPlan, build_bracket(), build_events(), build_modality() (+12 more)

### Community 44 - "Security and JWT Config"
Cohesion: 0.16
Nodes (12): Settings, generate_oauth_state(), get_platform_from_state(), is_valid_oauth_state(), test_oauth_state_round_trip(), auth_callback(), _login_error_redirect(), login_with_suap() (+4 more)

### Community 45 - "Modality Creation Tests"
Cohesion: 0.23
Nodes (4): make_adapter(), make_context(), make_valid_configuration(), TestCreateModalityAdapter

### Community 46 - "Notification API Endpoints"
Cohesion: 0.15
Nodes (11): RegisterDeviceTokenPort, RemoveDeviceTokenPort, FCMPushSenderAdapter, register_device_token(), remove_device_token(), get_personal_notifier(), get_push_sender(), get_register_device_token_port() (+3 more)

### Community 47 - "User Repository Access"
Cohesion: 0.13
Nodes (5): Gender, UserRepositoryAdapter, UserMapper, test_clear_atleta_updates_only_given_athletes_in_one_statement(), mk()

### Community 48 - "Development Deployment Workflow"
Cohesion: 0.08
Nodes (25): permissions, runs-on, steps, concurrency, cancel-in-progress, group, env, IMAGE (+17 more)

### Community 49 - "Production Deployment Workflow"
Cohesion: 0.08
Nodes (25): permissions, runs-on, steps, concurrency, cancel-in-progress, group, env, IMAGE (+17 more)

### Community 50 - "CI Pull Request Verification"
Cohesion: 0.08
Nodes (25): concurrency, cancel-in-progress, group, jobs, verify, name, on, pull_request (+17 more)

### Community 51 - "Audit Log Persistence"
Cohesion: 0.20
Nodes (5): AuditLogRepositoryPort, AuditLog, AuditLogRepositoryAdapter, AuditLogMapper, AuditLogEntity

### Community 52 - "Integration Test Fakes"
Cohesion: 0.11
Nodes (5): get_broadcaster_singleton(), _FakeMatchRepository, _FakeStateRepository, _PublishingMatchRepository, TestRealtimeSSEFlow

### Community 53 - "Tournament Draw Engine"
Cohesion: 0.15
Nodes (11): _build_first_round_pairs(), build_knockout_tree(), _build_round_robin_matches(), DrawPlan, GroupSpec, MatchSpec, _round_robin_pairs(), persist_draw_groups() (+3 more)

### Community 54 - "Group Standings Resolver"
Cohesion: 0.17
Nodes (8): _average(), _bucket_by(), _head_to_head_table(), order_group_standings(), resolve(), make_match(), make_team(), TestOrderGroupStandings

### Community 55 - "Knockout Draw Tests"
Cohesion: 0.21
Nodes (6): make_adapter(), make_bracket(), TestDrawKnockoutStageAdapter, make_adapter(), make_adapter(), TestUpdateMatchAdapter

### Community 57 - "JWT Authentication Utilities"
Cohesion: 0.18
Nodes (7): JWTProviderPort, extract_token_from_credentials(), validate_user_active(), verify_and_extract_user_id(), get_current_user(), get_current_user_id(), get_optional_current_user()

### Community 58 - "Match Event Endpoints"
Cohesion: 0.45
Nodes (19): MatchEventPublisher, _build_response(), delete_event(), end_penalty_shootout(), end_period(), end_set(), finish_match(), pause_clock() (+11 more)

### Community 60 - "Bracket Group Repository"
Cohesion: 0.28
Nodes (5): BracketGroup, BracketGroupRepositoryAdapter, BracketGroupMapper, BracketGroupEntity, test_insert_all_persists_batch_without_per_row_selects()

### Community 61 - "Season Modality Persistence"
Cohesion: 0.25
Nodes (3): SeasonModality, SeasonModalityRepositoryAdapter, SeasonModalityMapper

### Community 62 - "Live Ticket Adapters"
Cohesion: 0.26
Nodes (3): InvalidLiveTicketError, LiveTicketAdapter, TestLiveTicketAdapter

### Community 63 - "Auth Callback Tests"
Cohesion: 0.14
Nodes (9): _clean_overrides(), _client(), _login_port(), test_callback_exchanges_code_with_redirect_uri_of_platform(), test_invalid_state_redirects_to_login_with_generic_code(), test_suap_failure_redirects_without_leaking_details(), test_web_callback_never_puts_access_token_in_url_and_sets_cookie(), _Session (+1 more)

### Community 64 - "SUAP OAuth Integration"
Cohesion: 0.17
Nodes (4): SUAPOAuthAdapter, _suap(), test_attendance_url_has_trailing_slash_and_is_saved(), get_oauth_provider()

### Community 65 - "Device Token Registration"
Cohesion: 0.27
Nodes (4): RegisterDeviceTokenAdapter, DevicePlatform, make_context(), TestRegisterDeviceTokenAdapter

### Community 66 - "Personal Notification Tests"
Cohesion: 0.29
Nodes (5): PushSendResult, make_device_token(), make_notifier(), TestPersonalNotifier, slow_send()

### Community 67 - "Match Event Publisher Tests"
Cohesion: 0.36
Nodes (4): MatchTeamSnapshot, make_match(), make_publisher(), TestMatchEventPublisher

### Community 68 - "Bracket Creation Tests"
Cohesion: 0.37
Nodes (7): configure_happy_path(), make_adapter(), make_approved_teams(), make_context(), make_season(), TestCreateBracketAdapterSuccess, TestCreateBracketAdapterValidations

### Community 69 - "Team Listing Tests"
Cohesion: 0.32
Nodes (4): make_adapter(), make_context(), setup_extra_info_mocks(), TestListTeamsAdapter

### Community 70 - "Modality Model Mapping"
Cohesion: 0.22
Nodes (5): ModalityModelMapper, ModalityConfigurationResponse, ModalityCreateResponse, ModalityStatusResponse, ModalitySummaryResponse

### Community 72 - "Volleyball Configuration Persistence"
Cohesion: 0.35
Nodes (4): VolleyballModalityConfiguration, VolleyballModalityConfigurationRepositoryAdapter, VolleyballModalityConfigurationMapper, VolleyballModalityConfigurationEntity

### Community 73 - "Team Approval Tests"
Cohesion: 0.28
Nodes (4): confirmed_members(), make_adapter(), make_context(), TestApproveTeamAdapter

### Community 74 - "Team Details Tests"
Cohesion: 0.30
Nodes (4): make_adapter(), make_context(), make_open_season(), TestGetTeamDetailsAdapter

### Community 76 - "Scheduled Season Jobs"
Cohesion: 0.30
Nodes (8): SeasonStatus, run_open_seasons_job(), FakeSession, test_close_job_notifies_closed_season_after_commit(), test_open_job_does_not_deactivate_season_in_progress(), test_open_job_does_not_notify_when_commit_fails(), test_open_job_notifies_opened_season_after_commit(), test_open_job_opens_season_when_no_active_season()

### Community 77 - "App Lifecycle and Scheduler"
Cohesion: 0.20
Nodes (4): start_scheduler(), stop_scheduler(), health_check(), lifespan()

### Community 78 - "Active Season Retrieval"
Cohesion: 0.23
Nodes (4): GetActiveSeasonAdapter, NotFoundException, make_adapter(), TestGetActiveSeasonAdapter

### Community 79 - "Modality Configuration Persistence"
Cohesion: 0.34
Nodes (3): ModalityConfiguration, ModalityConfigurationRepositoryAdapter, ModalityConfigurationMapper

### Community 80 - "Team Invite Tests"
Cohesion: 0.37
Nodes (5): make_adapter(), make_context(), make_draft_team(), make_open_season(), TestGetTeamInviteInfoAdapter

### Community 81 - "Team Submission Tests"
Cohesion: 0.36
Nodes (4): make_adapter(), make_context(), make_open_season(), TestSubmitTeamAdapter

### Community 82 - "Round Information Logic"
Cohesion: 0.31
Nodes (4): build_round_info(), _depth_from_final(), make_match(), TestBuildRoundInfo

### Community 83 - "Season Management Tests"
Cohesion: 0.36
Nodes (3): make_adapter(), make_context(), TestManageSeasonAdapter

### Community 84 - "Match Broadcast Content"
Cohesion: 0.30
Nodes (3): CardType, broadcast_push_content(), MatchCardRequest

### Community 85 - "Season Finish Tests"
Cohesion: 0.36
Nodes (3): make_adapter(), make_context(), TestFinishSeasonAdapter

### Community 86 - "Registration Reopening Tests"
Cohesion: 0.38
Nodes (3): make_adapter(), make_context(), TestReopenRegistrationAdapter

### Community 87 - "Donation Confirmation Tests"
Cohesion: 0.36
Nodes (3): make_adapter(), make_context(), TestConfirmDonationAdapter

### Community 88 - "Project Documentation ADRs"
Cohesion: 0.20
Nodes (11): ADR 0001 - Estratégia do Cronômetro, UC001 - Criar Temporada, UC008 - Submeter Equipe, UC009 - Aprovar Equipes, Confirmar Doação, Criar Chaveamento, Gerenciar Chaveamento, Iniciar Partida (+3 more)

### Community 89 - "Device Token Removal"
Cohesion: 0.47
Nodes (3): RemoveDeviceTokenAdapter, make_context(), TestRemoveDeviceTokenAdapter

### Community 90 - "Modality Activation Tests"
Cohesion: 0.49
Nodes (9): UpdateModalityActiveAdapter, make_adapter(), make_context(), make_modality(), test_activate_modality_logs_activated_action(), test_deactivate_modality_saves_and_logs_audit(), test_update_modality_active_is_idempotent_when_state_unchanged(), test_update_modality_active_raises_not_found_when_missing() (+1 more)

### Community 91 - "Submission Eligibility Logic"
Cohesion: 0.33
Nodes (3): evaluate_submit_eligibility(), make_open_season(), TestEvaluateSubmitEligibility

### Community 92 - "JWT Provider Tests"
Cohesion: 0.31
Nodes (3): JWTProviderAdapter, test_access_token_round_trip_and_rejects_garbage(), get_jwt_provider()

### Community 93 - "Match Start Tests"
Cohesion: 0.49
Nodes (4): make_adapter(), make_match(), make_team(), TestStartMatchAdapter

### Community 94 - "Season Details Tests"
Cohesion: 0.38
Nodes (3): make_adapter(), make_context(), TestGetSeasonDetailsAdapter

### Community 95 - "Member Removal Tests"
Cohesion: 0.40
Nodes (3): make_adapter(), make_context(), TestRemoveMemberAdapter

### Community 97 - "Leave Team Tests"
Cohesion: 0.42
Nodes (3): make_adapter(), make_context(), TestLeaveTeamAdapter

### Community 98 - "Member Exit Tests"
Cohesion: 0.42
Nodes (3): make_adapter(), make_context(), TestLeaveTeamAdapter

### Community 101 - "Season Creation API Tests"
Cohesion: 0.31
Nodes (6): client_and_port(), _form_data(), test_accepts_fields_and_rules_document_in_one_request(), test_rejects_blank_name_with_422(), test_rules_document_is_optional(), require_monitor()

### Community 102 - "Close Registration Adapter Tests"
Cohesion: 0.44
Nodes (3): make_adapter(), make_context(), TestCloseRegistrationAdapter

### Community 103 - "Token Refresh Security Tests"
Cohesion: 0.56
Nodes (7): _service(), _service_with_tokens(), test_logged_out_token_is_rejected_without_killing_other_sessions(), test_retry_within_grace_issues_tokens_without_killing_sessions(), test_reuse_after_grace_still_revokes_all_sessions(), test_reusing_rotated_token_revokes_all_sessions_and_commits(), _token()

### Community 106 - "Bracket Resorting Adapter Tests"
Cohesion: 0.54
Nodes (3): make_adapter(), make_bracket(), TestResortBracketAdapter

### Community 114 - "Season and Match Documentation"
Cohesion: 0.40
Nodes (4): Plano de Execução — Intercurso IFRN Backend, UC001: Criar Temporada, UC002: Gerenciar Temporada, Match Domain Entity

## Knowledge Gaps
- **18 isolated node(s):** `intercurso-ifrn-backend`, `Match Domain Entity`, `UC002: Gerenciar Temporada`, `Visualizar Partida em Tempo Real`, `ADR 0004 - Modelo de Acesso` (+13 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 632 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **167 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Context` connect `Generic Context Operations` to `Bracket Management Adapters`, `Test Mocks and Stubs`, `Match Control Ports`, `Season and Team Adapters`, `User Profile Management`, `Database Session Dependencies`, `Bracket Statistics and Status`, `Modality Management`, `Season Validation Tests`, `Domain Validation Rules`, `Season Repository Access`, `Authentication and OAuth Ports`, `Knockout Stage Drawing`, `Match Metadata Enums`, `Bracket Operation Ports`, `Live Ticket Management`, `Penalty Shootout Tests`, `Team Creation Tests`, `Team Status Management`, `Season Progress Queries`, `Security and JWT Config`, `Modality Creation Tests`, `Notification API Endpoints`, `Knockout Draw Tests`, `Match Event Endpoints`, `Match Persistence Operations`, `Device Token Registration`, `Bracket Creation Tests`, `Team Listing Tests`, `Team Membership Queries`, `Team Approval Tests`, `Team Details Tests`, `Active Season Retrieval`, `Team Invite Tests`, `Team Submission Tests`, `Season Management Tests`, `Season Finish Tests`, `Registration Reopening Tests`, `Donation Confirmation Tests`, `Device Token Removal`, `Modality Activation Tests`, `Match Start Tests`, `Season Details Tests`, `Member Removal Tests`, `Token Lifecycle Management`, `Leave Team Tests`, `Member Exit Tests`, `Public Match Adapter Tests`, `Close Registration Adapter Tests`, `Bracket Listing Adapter Tests`, `Bracket Resorting Adapter Tests`, `Bracket Details Adapter Tests`, `Season Listing Adapter Tests`, `Match Deletion Adapter Tests`, `Bracket Configuration Suggestion Tests`?**
  _High betweenness centrality (0.119) - this node is a cross-community bridge._
- **Are the 150 inferred relationships involving `Context` (e.g. with `CreateBracketAdapter` and `DeleteMatchAdapter`) actually correct?**
  _`Context` has 150 INFERRED edges - model-reasoned connections that need verification._
- **What connects `intercurso-ifrn-backend`, `Match Domain Entity`, `UC002: Gerenciar Temporada` to the rest of the system?**
  _18 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Bracket Management Adapters` be split into smaller, more focused modules?**
  _Cohesion score 0.05177993527508091 - nodes in this community are weakly interconnected._
- **Why does `BusinessException` connect `Bracket Management Adapters` to `Test Mocks and Stubs`, `Season and Team Adapters`, `Bracket Configuration Logic`, `Bracket Statistics and Status`, `Modality Management`, `Season Validation Tests`, `Domain Validation Rules`, `Authentication and OAuth Ports`, `Refresh Token Management`, `Knockout Stage Drawing`, `Match Metadata Enums`, `Bracket Operation Ports`, `Generic Context Operations`, `Push Notification Service`, `Penalty Shootout Tests`, `Team Creation Tests`, `Device Token Management`, `Team Status Management`, `Season Progress Queries`, `Security and JWT Config`, `Modality Creation Tests`, `Notification API Endpoints`, `Knockout Draw Tests`, `JWT Authentication Utilities`, `Match Persistence Operations`, `Auth Callback Tests`, `SUAP OAuth Integration`, `Device Token Registration`, `Bracket Creation Tests`, `Team Listing Tests`, `Team Membership Queries`, `Team Approval Tests`, `Team Details Tests`, `R2 Storage Integration`, `Active Season Retrieval`, `Team Invite Tests`, `Team Submission Tests`, `Season Management Tests`, `Season Finish Tests`, `Registration Reopening Tests`, `Donation Confirmation Tests`, `Device Token Removal`, `Modality Activation Tests`, `JWT Provider Tests`, `Match Start Tests`, `Season Details Tests`, `Member Removal Tests`, `Token Lifecycle Management`, `Leave Team Tests`, `Member Exit Tests`, `Public Match Adapter Tests`, `Close Registration Adapter Tests`, `Token Refresh Security Tests`, `Bracket Listing Adapter Tests`, `Bracket Resorting Adapter Tests`, `Bracket Details Adapter Tests`, `Match Deletion Adapter Tests`, `Bracket Configuration Suggestion Tests`?**
  _High betweenness centrality (0.072) - this node is a cross-community bridge._
- **Are the 121 inferred relationships involving `BusinessException` (e.g. with `CreateBracketAdapter` and `DeleteMatchAdapter`) actually correct?**
  _`BusinessException` has 121 INFERRED edges - model-reasoned connections that need verification._
- **Should `Test Mocks and Stubs` be split into smaller, more focused modules?**
  _Cohesion score 0.06831955922865014 - nodes in this community are weakly interconnected._