# Octoha Implementation Research Findings

## Context Summary

Researched comprehensive implementation requirements for Octoha - a Home Assistant custom integration for Octopus Energy smart meter data. The project has existing documentation including PRD, ADR, component architecture, and ERD. The goal is to replace broken Bright/SMETS integration with reliable, open-source solution.

## Key API Patterns from open-octopus

### Authentication Flow
- **GraphQL Token Management**: Uses mutation `obtainKrakenToken` with API key to get 55-minute tokens
- **Token Refresh**: Automatic refresh before expiry with 5-minute buffer
- **HTTP Client**: Currently uses `httpx.AsyncClient` (needs adaptation to HA's `aiohttp`)

### API Architecture (Dual API Strategy)
- **GraphQL API**: `https://api.octopus.energy/v1/graphql/`
  - Account info, balance, dispatches
  - Live power consumption (Home Mini)
  - Intelligent Octopus dispatch slots  
  - Saving Sessions/Free Electricity events
  - Smart device registration
- **REST API**: `https://api.octopus.energy/v1`
  - Half-hourly consumption data (electricity/gas)
  - Tariff rates and standing charges
  - Historical consumption data

### Key Client Methods (from open-octopus client.py)
```python
# Authentication
async def _get_token(self) -> str
async def _graphql(self, query: str, variables: dict) -> dict

# Account & Consumption  
async def get_account(self) -> Account
async def get_consumption(self, periods=48) -> list[Consumption]
async def get_gas_consumption(self, periods=48) -> list[GasConsumption]
async def get_daily_usage(self, days=7) -> dict[str, float]

# Tariffs & Rates
async def get_tariff(self, region="J") -> Optional[Tariff]
async def get_current_rate(self, tariff: Tariff) -> Rate

# Smart Features
async def get_dispatches(self) -> list[Dispatch]
async def get_dispatch_status(self) -> DispatchStatus
async def get_live_power(self) -> Optional[LivePower]
async def get_saving_sessions(self) -> list[SavingSession]
```

### Data Models (from open-octopus models.py)
- **Account**: `number`, `balance`, `name`, `status`, `address`
- **Consumption**: `start`, `end`, `kwh`
- **GasConsumption**: `start`, `end`, `kwh`, `m3` (with m³→kWh conversion factor 11.1868)
- **Tariff**: `name`, `product_code`, `standing_charge`, `rates`, `off_peak_rate`, `peak_rate`
- **Rate**: `rate`, `is_off_peak`, `period_end`, `next_rate`
- **Dispatch**: `start`, `end`, `source` ("smart-charge"/"bump-charge")
- **DispatchStatus**: `is_dispatching`, `current_dispatch`, `next_dispatch`
- **LivePower**: `demand_watts`, `read_at`, `consumption_kwh`

## Home Assistant Integration Best Practices

### Config Flow Patterns
- **Manifest Requirements**: `config_flow: true`, `iot_class: "cloud_polling"`
- **Step Structure**: `async_step_user`, `async_step_reconfigure`, `async_step_reauth`
- **Unique ID Management**: Required for discovery, prevents duplicate entries
- **Validation**: API key validation in config flow before entry creation
- **Reconfiguration**: Support options flow for intervals, thresholds without removing integration

### DataUpdateCoordinator Pattern
- **Multiple Coordinators**: Separate coordinators for different data types/intervals
- **Error Handling**: `ConfigEntryAuthFailed` for auth errors triggers reauth flow
- **Update Intervals**: 
  - Electricity/Gas: 5 minutes (balance API limits vs freshness)
  - Tariff: 30-60 minutes (rates change infrequently except Agile)
  - Live Power: 30 seconds (near real-time)
  - Dispatches: 5 minutes (dispatch schedules can change)

### Entity Platform Structure
- **Sensor Entities**: For consumption, rates, costs, power readings
- **Binary Sensors**: For dispatch active/inactive, off-peak periods, saving sessions
- **Device Registration**: Single device representing the Octopus Energy integration
- **Entity Naming**: `sensor.octoha_{meter_type}_{measurement}` convention
- **Attributes**: Include metadata (last_updated, data_source, meter_serial, attribution)

## Proposed Task Breakdown

### Phase 1: Foundation & API Integration (Week 1-2)
1. **Extract & Adapt API Client**
   - Extract client.py and models.py patterns from open-octopus
   - Replace httpx with aiohttp + HA session management
   - Implement token management with HA credential storage
   - Add comprehensive error handling

2. **Core Integration Structure**
   - Implement manifest.json and const.py
   - Create basic config flow with API key validation
   - Set up coordinator.py with base coordinator class
   - Add unit tests for API client

### Phase 2: Core Consumption Data (Week 3-4)
3. **Electricity Data Coordinator**
   - Implement ElectricityCoordinator with 5-minute updates
   - REST API integration for consumption data
   - Daily usage aggregation and current consumption

4. **Sensor Entities**
   - Create sensor.py with electricity consumption sensors
   - Entity naming convention and attributes
   - Integration with HA Energy Dashboard

### Phase 3: Gas & Tariff Data (Week 5-6)
5. **Gas Data Coordinator**
   - Implement GasCoordinator with SMETS1/SMETS2 handling
   - m³ to kWh conversion logic
   - Gas consumption sensors

6. **Tariff Coordinator**
   - Implement TariffCoordinator with rate tracking
   - Time-of-use rate calculations
   - Binary sensors for off-peak periods

### Phase 4: Smart Features & Polish (Week 7-8)
7. **Dispatch Coordinator**
   - Intelligent Octopus dispatch tracking
   - Binary sensors for charging status
   - Automation event triggers

8. **Live Power & Options**
   - Live power coordinator (Home Mini support)
   - Options flow for intervals and thresholds
   - Configuration reconfiguration support

### Phase 5: Testing & Release (Week 9-10)
9. **Integration Testing**
   - Comprehensive test coverage
   - Error handling validation
   - Reauth flow testing

10. **Documentation & Release**
    - User documentation and setup guide
    - HACS manifest and repository structure
    - Beta testing and refinement

## Dependencies Identified

### Required for Implementation
- **open-octopus patterns**: Client and model extraction (MIT licensed)
- **HA Core Dependencies**: aiohttp, voluptuous for config validation
- **API Access**: Valid Octopus Energy API key and account
- **Meter Requirements**: MPAN/MPRN and meter serials for consumption data

### Optional/Nice-to-Have
- **Home Mini Device**: Required for live power functionality
- **Intelligent Octopus Tariff**: Required for dispatch features
- **Multiple Meters**: For users with both electricity and gas smart meters

## Risks and Unknowns

### Technical Risks
1. **GraphQL API Stability**: Unofficial API may change without notice
2. **Token Management**: Authentication failures need graceful handling
3. **Data Availability**: Smart meter data delays vary by region/provider
4. **Rate Limiting**: API throttling could affect update frequencies

### Implementation Gaps
1. **Error Recovery**: Need spike on API outage handling patterns
2. **Migration**: Config entry version migration strategy needed
3. **Multi-Property**: Support for users with multiple Octopus accounts (P2)
4. **Gas Data Format**: Validation needed for different meter types

## Recommended Success Criteria

### Technical Validation
- Gas readings match IHD display exactly (100% accuracy target)
- Electricity data accurate within 1 hour of consumption
- Zero unhandled exceptions in 7-day continuous operation
- Config flow validates credentials before completion
- All core entities available within 30 minutes of setup

### User Experience
- Setup time <5 minutes from HACS install to working dashboard
- Clear error messages for invalid credentials or missing meters
- Reconfiguration without data loss via options flow
- Integration with HA Energy Dashboard out-of-the-box

## Additional Resources

### Code References
- [open-octopus repository](https://github.com/abracadabra50/open-octopus) - API patterns reference
- [HA Developer Docs - Config Flow](https://developers.home-assistant.io/docs/config_entries_config_flow_handler)
- [HA Developer Docs - DataUpdateCoordinator](https://developers.home-assistant.io/docs/integration_fetching_data)
- [HA Developer Docs - Integration Manifest](https://developers.home-assistant.io/docs/creating_integration_manifest)

### Attribution Requirements
- MIT license attribution for open-octopus patterns in LICENSE file
- Credit open-octopus in README and code comments
- Link to original repository for reference

This research provides sufficient context to begin implementation with 80%+ confidence in the approach and technical feasibility.
