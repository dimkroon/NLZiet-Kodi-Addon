# NLZiet Kodi Addon — Comprehensive Changes List
## Complete Documentation of All Changes (v0.0.2 → v1.0.0)

---

## SUMMARY OF VERSIONS

- **v1.0.0** (2026-04-06): Stable release with full OAuth2, EPG display, performance optimization
- **v0.0.9** (2026-04-04): Token-based authentication, UI/UX overhaul, performance caching
- **v0.0.8** (2026-04-02): Localization, TV shows, documentaries, subtitle handling
- **v0.0.7** (2026-03-25): 
- **v0.0.6** (2026-03-25): TV shows, documentaries, account integration, logout
- **v0.0.4** (2026-03-19): Search, grouped results, landscape artwork
- **v0.0.2** (2026-03-19): Search implementation

---

## FILE-BY-FILE CHANGES

### 1. **default.py** — Main Plugin Handler

#### ADDED

- **Global API Instance Cache** (lines 21-23, 32-43)
  - `_api_cache`: Caches NLZietAPI instance for 5 minutes (300 seconds)
  - `get_api_instance()`: Centralized API access with TTL-based cache
  - Reduces disk I/O and initialization overhead on every menu interaction
  - Enables near-instant context menu operations

- **Short-Lived Channel Menu Cache** (lines 24-27, 48-89)
  - `_channel_menu_cache_data`, `_channel_menu_cache_epg`, `_channel_menu_cache_time`: 45-second cache
  - `get_channels_menu_data()`: Caches channels + EPG together
  - Makes return-from-playback instant by avoiding re-fetch of channels/EPG
  - `get_current_programs()` call integrated into channels menu function

- **Smart Artwork Assignment System** (lines 298-430)
  - `_optimize_image_url()` (lines 298-321): Requests 3840px width for 4K-quality fanart instead of default 1280px
  - `_pick_landscape_thumb()` (lines 323-369): Extracts landscape (16:9) images from content
  - `_pick_portrait_thumb()` (lines 372-410): Extracts portrait (2:3) images from content  
  - `_set_smart_artwork()` (lines 413-430): Assigns images by aspect ratio (fanart for landscape, poster for portrait)
  - Prevents face-cutting and image stretching by using correct aspect ratios per Kodi art key

- **Live TV EPG Display** (lines 2242-2290 in `browse_category()`)
  - "Nu live:" current program title with time range (HH:MM-HH:MM)
  - "Straks:" next program title with time range
  - Handles missing times gracefully with fallback formatting
  - Dutch localization ("Nu live", "Straks") for consistency

- **Live TV Context Menu Prevention** (lines 218-245)
  - `ResumeTime`, `TotalTime`, `IsLive` properties set for live channels
  - Removes "Resume from" and "Play from beginning" context menu options on live TV
  - Clears resume position from info dict for live streams
  - Direct playback via `IsLive` property awareness

- **Localization System** (lines 99-180)
  - Complete TRANSLATIONS dict with 60+ entries (Dutch/English)
  - `get_string()` function for multilingual UI
  - All menu labels, notifications, and dialogs now bilingual
  - Dutch as primary, English as fallback

- **Dialog-Based Login UI** (lines 1428-1465)
  - `show_login_dialog()`: Modern Kodi dialog input for email/password
  - User input via xbmcgui.Dialog.input() instead of addon settings
  - Credentials never exposed in Settings menu
  - Pre-fill support for retry flow

- **Enhanced Login Flow with Retry** (lines 1467-1626)
  - `do_login()`: 3-attempt retry loop with user confirmation
  - PKCE authorize + token exchange after form login
  - Credential save options (tokens-only recommended, or tokens+password for auto-refresh)
  - Clear error/status messages for each stage
  - Updates cached API instance immediately after successful login
  - Silent account info refresh after login
  - Main menu container refresh to show authenticated items

- **Channel Optimization** (lines 2218-2226)
  - Skips `/v9/content/detail/` requests for channels (endpoint not supported)
  - Prevents 404 errors and improves menu load time for channel browsing
  - Special handling in `browse_category()` to skip detail fetch for channels

#### CHANGED

- **API Instance Management** (throughout)
  - All menu functions now call `get_api_instance()` instead of creating new NLZietAPI objects
  - Affects: `browse_placementtiles()`, `browse_recently_added()`, `browse_search()`, `manages_profiles()`, `browse_my_list()`, `browse_category()`, and 15+ other functions
  - Cache TTL: 300 seconds (5 minutes)

- **Image URL Handling** 
  - All image URLs now request 3840px width via `_optimize_image_url()`
  - Applied to all content types: movies, series, documentaries, TV shows, channels, live TV

- **Settings Structure Conversion** (addon.xml and resources/settings.xml)
  - Migrated to Kodi v19+ `version="1"` converted settings format
  - Section/Category/Group/Setting/Control hierarchy
  - Dutch-only labels (removed language switching in settings UI)
  - Account section with read-only subscription fields

#### FIXED

- **EPG Data Parsing** (lines 2242-2290)
  - Fixed nested `channel`/`programLocations` response structure parsing
  - Program titles, times, descriptions correctly extract from nested objects
  - Supports both flat and nested response formats

- **EPG Program Selection** (lines 2267-2289)
  - Fixed logic to prioritize currently-playing programs over future/past programs
  - Proper timestamp comparison with current time
  - Handles timezone-aware timestamps

- **Context Menu on Live TV** (lines 241-245)
  - Properly sets `ResumeTime='0'`, `TotalTime='0'`, `IsLive='true'` to prevent context menu
  - Info dict modified to remove resume position for live content

- **Channel Menu Performance** (removed 1-second sleep)
  - Removed unnecessary per-channel fallback logic that caused delays
  - Instant return from live TV cancel via channel cache refresh

- **Undefined Variable Issue**
  - `api` object guaranteed to be initialized in `browse_category()` and all menu functions via `get_api_instance()`
  - Proper error handling with fallback to direct NLZietAPI creation if cache fails

---

### 2. **resources/lib/nlziet_api.py** — API Wrapper

#### ADDED

- **Token-Based Authentication System** (lines 98-140, 450-650+)
  - `self.tokens`: Dict to store access_token, refresh_token, expires_at
  - `self.token_file`: Persistent token storage (special://profile/addon_data/.../tokens.json)
  - `load_tokens()`, `save_tokens()`: Load/save from disk
  - Automatic token loading on API initialization

- **OAuth2 PKCE Authorization Flow** (lines 1888-2100+)
  - `perform_pkce_authorize_and_exchange()`: Full PKCE code flow
  - Generates `code_challenge` and `code_verifier` (SHA256)
  - Opens browser for user authorization at `/connect/authorize`
  - Monitors for callback at `/callback`
  - Exchanges code for tokens at `/connect/token`
  - Handles both `openid api offline_access` (preferred) and `openid api` (fallback) scopes
  - Stores tokens in `self.tokens` dict
  - Auto-saves tokens to disk via `save_tokens()`

- **Automatic Token Refresh** (lines 1803-1870)
  - `get_valid_token()`: Returns valid access token or refreshes if expired
  - 30-second expiry buffer for proactive refresh
  - `refresh_tokens()`: Attempts refresh_token if available
  - Fallback to cookie-based PKCE if refresh_token unavailable
  - Supports both token-based and cookie-session renewal

- **Cookie Session Detection** (lines 267-279)
  - `_has_cookie_session()`: Checks for presence of session cookies (idSrv, idSrv.session, etc.)
  - Enables cookie-based PKCE renewal when tokens not available

- **EPG Functions** (lines 2844-3115+)
  - `get_epg_channels()`: Returns EPG channel list from `/v9/epg/channels`
  - `get_current_programs()`: Fetches program locations for given channel IDs via `/v9/epg/programlocations`
  - Handles nested `channel`/`programLocations` response format
  - Extracts current and next programs with start/end times
  - Returns nested `epg_map[channel_id] = {'programs': [...], 'current': {...}, 'next': {...}}`

- **Documentaries Support** (lines 1118-1188)
  - `get_documentaries()`: Fetches documentary series using `/v9/recommend/filtered?category=Programs&genre=Documentary`
  - Handles `content` field wrapper in response (Series items wrapped in data array)
  - Extracts type field to identify Series vs Episode
  - Returns clean series items with proper IDs for series_detail routing

- **Enhanced Video/Series Parsing** (lines 768-857)
  - `get_videos()`: Updated to extract and return `type` field
  - Properly identifies Series vs Episode items
  - Extracts from `content` or `item` wrapper fields
  - Includes optional seasons metadata extraction
  - Type defaults to 'Episode' if not present in response

- **Stream Cookie Migration** (lines 71-102)
  - `stream_cookies` JSON → LWPCookieJar format automatic conversion
  - Maintains backward compatibility with old cookie format

- **Debug Authentication State** (throughout)
  - `_debug_auth_state()`, `_append_debug()`: Debug logging for auth flows
  - Persistent HTTP debug log at special://profile/addon_data/.../nlziet_http_debug.txt

#### CHANGED

- **Scope Handling in PKCE** (line 1910-1913)
  - Tries `openid api offline_access` first (to obtain refresh_token)
  - Falls back to `openid api` if offline_access not granted
  - Token exchange retries without explicit scope if needed

- **Token Exchange Retry Logic** (line 1638-1640)
  - Detects when offline_access requested but no refresh_token returned
  - Logs scope mismatch for debugging

- **Session Persistence**
  - Tokens saved immediately after exchange via `save_tokens()`
  - Cookies persisted in LWPCookieJar format (HTTP standard)
  - Both survive Kodi restarts automatically

#### FIXED

- **Series/Episode Type Detection**
  - `get_videos()` now extracts `type` field from API response
  - Allows `browse_category()` to properly detect Series items and route to `series_detail` mode
  - Fixes issue where TV shows like "Sexotisch" tried to play instead of showing seasons

- **Documentary Response Parsing**
  - Fixed extraction from wrapped `content` field (not `item`)
  - Simplified parsing, removed unnecessary expiration date extraction
  - Proper type field extraction for series identification

- **Token Expiry Handling**
  - Added `expires_at` field to track expiration in Unix timestamp
  - 30-second buffer prevents stale token usage
  - Proactive renewal before expiry occurs

- **Undefined Token References**
  - Safe handling in `get_valid_token()` when no refresh_token present
  - Graceful fallback to cookie-based PKCE
  - No NameError on missing token fields

---

### 3. **addon.xml**

#### CHANGED

- **Version**: Bumped to `1.0.0` (from 0.0.7)
- **Dependencies**: Added explicit `script.module.inputstreamhelper` v0.6.0 requirement
- **Metadata**: Dutch-only summary/description (removed language variants)
- **Assets**: Added fanart reference to `resources/media/background.jpg`

#### REMOVED

- **Language Variants**: Removed English summary `lang="en"`

---

### 4. **resources/settings.xml**

#### ADDED

- **Account Section** with read-only fields (lines 7-46):
  - `subscription_name`: Displays subscription plan name
  - `subscription_expires`: Shows expiration date
  - `max_devices`: Maximum concurrent devices
  - `subscription_type`: Subscription tier/plan type
  - `logout_button`: Action button to sign out

- **Converted Settings Format** (`version="1"`)
  - Kodi v19+ section/category/group/setting/control hierarchy
  - Explicit controls with format specifications
  - Proper label IDs for string localization

#### CHANGED

- **Settings Structure**: Migrated from legacy format to v1 converted format
- **Language Support**: Dutch-only UI (removed English language switching controls)

---

### 5. **resources/language/resource.language.nl_nl/strings.po** and **strings.xml**

#### ADDED

- **Account Section Labels** (30 entries added):
  - Account info strings ("Accountgegevens", etc.)
  - Subscription-related labels
  - Login/logout messages
  - Button labels
  - Help text and descriptions

- **EPG Labels**:
  - "Nu live" (currently playing)
  - "Straks" (next program)

- **Localization Entries**: 60+ total Dutch strings across:
  - Menu items (Series, Movies, TV Shows, Documentaries, My List, Channels, Profiles, Search)
  - Notifications (Login successful, session token obtained, logout confirmation)
  - Dialog messages (credential save options, token renewal messages)
  - Settings labels (subscription, profiles, account info)

#### CREATED

- **resource.language.nl_nl/strings.po**: New PO format for converted settings
- **resource.language.en_gb/strings.po**: English fallback for settings UI

---

### 6. **resources/media/** — Icons and Artwork

#### ADDED

- `background.jpg`: Addon fanart/background image (3840x2160px or similar)
- `menu_logout.png`: Dedicated logout button icon (referenced in main menu)
- `emoji_google_active.png`: Green checkmark icon for active profile selection
- `emoji_google_inactive.png`: Gray icon for inactive profiles

---

### 7. **CHANGELOG.md**

#### STRUCTURE

- **[Unreleased]** section documenting all v1.0.0 changes
- **[1.0.0]** release entry (2026-04-06)
- **[0.0.9]** through **[0.0.2]** historical entries

#### DOCUMENTED CHANGES

- All EPG, authentication, performance, and localization changes
- Each change categorized as Added/Fixed/Changed/Removed
- Notes section explaining technical details (PKCE, cookie format, cache timeouts, etc.)

---

## FEATURE SUMMARY BY CATEGORY

### 1. **Authentication & Session Management** (v0.0.9 →  v1.0.0)

| Feature | Status | File(s) | Details |
|---------|--------|---------|---------|
| OAuth2 PKCE Flow | Added | nlziet_api.py | `/connect/authorize` + `/connect/token` endpoints |
| Dialog-Based Login | Added | default.py | Modern Kodi input UI, no settings exposure |
| Token Persistence | Added | nlziet_api.py | tokens.json with auto-load on startup |
| Auto-Token Refresh | Added | nlziet_api.py | `get_valid_token()` with 30-sec buffer |
| Cookie Session Renewal | Added | nlziet_api.py | Fallback PKCE when refresh_token unavailable |
| Optional Credential Save | Added | default.py | Users choose tokens-only or tokens+password |
| Logout Confirmation | Added | default.py | Two-step logout with "Keep My List" option |
| Protected Menu Items | Added | default.py | Series, Movies, TV Shows, Search, My List hidden when logged out |
| Account Info Display | Added | default.py, settings.xml | Read-only subscription/expiry/devices in Settings |
| Silent Account Refresh | Added | default.py | Background refresh on startup & after login |

### 2. **EPG (Electronic Program Guide)** (v0.0.9 → v1.0.0)

| Feature | Status | File(s) | Details |
|---------|--------|---------|---------|
| Live Program Display | Added | default.py | "Nu live:" current + "Straks:" next program |
| EPG Time Formatting | Added | default.py | HH:MM-HH:MM time ranges for broadcast windows |
| EPG API Integration | Added | nlziet_api.py | `get_current_programs()` + `/v9/epg/programlocations` |
| EPG Caching | Added | default.py | 45-second cache for instant menu returns |
| Nested Response Parsing | Fixed | nlziet_api.py | Handles channel/programLocations wrapper format |
| Program Selection Logic | Fixed | nlziet_api.py | Prioritizes current over future/past programs |
| Context Menu Prevention | Fixed | default.py | `ResumeTime`, `TotalTime`, `IsLive` properties |

### 3. **Performance & Optimization** (v0.0.9 → v1.0.0)

| Feature | Status | File(s) | Details |
|---------|--------|---------|---------|
| Global API Cache | Added | default.py | 5-minute TTL, eliminates disk I/O per menu |
| Channel Menu Cache | Added | default.py | 45-second fast cache for instant returns |
| High-Resolution Fanart | Added | default.py | Requests 3840px instead of 1280px (4K quality) |
| Smart Artwork Assignment | Added | default.py | Aspect-ratio aware: landscape→fanart, portrait→poster |
| Channel Skip Optimization | Added | default.py | Skips unsupported `/v9/content/detail/` for channels |
| Sleep Removal | Fixed | default.py | Removed 1-second delay on live TV cancel |
| Per-Channel Fallback Removal | Removed | nlziet_api.py | Eliminated unnecessary retry logic causing delays |

### 4. **UI/UX Improvements** (v0.0.8 → v1.0.0)

| Feature | Status | File(s) | Details |
|---------|--------|---------|---------|
| Fanart Support | Added | addon.xml, default.py | Menu-level background image assignment |
| Icon Assets | Added | resources/media/ | Logout, active/inactive profile icons |
| Dutch Localization | Added | language files | 60+ strings for complete Dutch UI |
| English Fallback | Added | resource.language.en_gb/ | English translations for addon settings |
| Settings Migration | Changed | settings.xml | Kodi v19+ v1 converted format |
| Dutch-Only Settings | Changed | default.py | Removed language switching from settings UI |
| Subscription Display | Added | settings.xml | Read-only account fields (subscription/expiry/devices) |
| Profile Icons | Added | resources/media/ | Green/gray icons for active/inactive profiles |

### 5. **Content Browsing** (v0.0.6 → v0.0.9)

| Feature | Status | File(s) | Details |
|---------|--------|---------|---------|
| TV Shows Section | Added | default.py | `/v9/recommend/withcontext?contextName=allPopularPrograms` |
| Documentary Section | Added | default.py | `/v9/recommend/filtered?category=Programs&genre=Documentary` |
| TV Show Genre Categories | Added | nlziet_api.py | 18 genre categories (Comedy, Drama, Sports, etc.) |
| Series Type Detection | Fixed | nlziet_api.py | Extracts `type` field to identify Series vs Episode |
| Documentary Series Routing | Fixed | default.py | Routes Series to `series_detail` (folder), not play |
| Content Wrapping Handling | Fixed | nlziet_api.py | Handles `content` field wrapper in responses |

### 6. **DRM & Playback** (v0.0.9 → v1.0.0)

| Feature | Status | File(s) | Details |
|---------|--------|---------|---------|
| InputStream Helper | Added | default.py | `script.module.inputstreamhelper` integration |
| Dynamic Device Selection | Added | default.py | Resolves inputstream.adaptive via helper |
| Widevine Support | Added | default.py | `com.widevine.alpha` DRM configuration |
| MaCap Support | Added | default.py | Enables proprietary DRM via helper |
| Stream Headers | Added | default.py | Passes custom headers to inputstream.adaptive |
| Subtitle Handling | Added | default.py | Subtitle properties prevent auto-loading from manifest |

---

## CUMULATIVE STATS

### Code Changes

| Metric | Count |
|--------|-------|
| Functions Added/Modified | 40+ |
| Localization Entries Added | 60+ |
| New API Methods | 8+ |
| Cache Systems Introduced | 2 (API, channels EPG) |
| Settings Fields Added | 10+ |
| Icon Assets Created | 4+ |

### Files Modified

| File | Changes |
|------|---------|
| default.py | 10,000+ lines, 40+ functions |
| nlziet_api.py | 3,000+ lines, 8+ new methods |
| addon.xml | Version, dependencies |
| settings.xml | Full structure migration |
| language files | 60+ new strings |
| CHANGELOG.md | Complete documentation |

---

## GITHUB ISSUES RESOLVED

The following issues/problems are addressed by these changes:

1. ✅ **Missing EPG on Live TV** — Fixed nested response parsing, added current/next program display
2. ✅ **Wrong Program Showing** — Fixed EPG selection logic to prioritize currently-playing programs
3. ✅ **Context Menu on Live TV** — Prevented "Resume from/Play from beginning" via IsLive property
4. ✅ **Small/Pixelated Fanart** — Requests 3840px instead of 1280px for 4K quality
5. ✅ **Face-Cutting on Images** — Smart artwork assignment separates landscape/portrait by aspect ratio
6. ✅ **Slow Menu Performance** — Added 5-minute API cache + 45-second channel EPG cache
7. ✅ **Delayed Live TV Cancel** — Removed 1-second sleep and per-channel fallback logic
8. ✅ **Documentary Playback Fail** — Fixed series/episode routing via type field detection
9. ✅ **TV Show Playback Fail** — Added type field extraction to identify Series items
10. ✅ **Undefined Variables** — Centralized API initialization via `get_api_instance()`
11. ✅ **Settings UI Blank** — Migrated to v1 converted format with proper string catalogs
12. ✅ **Channel 404 Errors** — Skip unsupported `/v9/content/detail/` for channels
13. ✅ **No Token Refresh** — Full PKCE + auto-refresh with cookie-session fallback
14. ✅ **No Subscription Display** — Added account info section in Settings with read-only fields

---

## BACKWARD COMPATIBILITY

✅ **Fully Backward Compatible**

- Old cookie format (`stream_cookies`) automatically migrated to LWPCookieJar
- Settings migration handled transparently for existing users
- Language files fallback to English if Dutch unavailable
- API cache gracefully handles failures with direct API creation fallback
- All new features are opt-in (account info display, token refresh, etc.)

---

## TESTING NOTES

Key test scenarios covered:

1. ✅ Fresh login flow (dialog UI + PKCE token exchange)
2. ✅ Saved credentials auto-login (optional password storage)
3. ✅ Token expiry + auto-refresh with fallback to PKCE
4. ✅ Cookie-session PKCE renewal (offline_access scope fallback)
5. ✅ EPG display with current/next programs (including missing times)
6. ✅ Live TV context menu prevention (ResumeTime/IsLive properties)
7. ✅ Smart artwork assignment (portrait vs landscape)
8. ✅ Series vs Episode routing (type field detection)
9. ✅ Cache expiry and refresh (5-min API, 45-sec EPG)
10. ✅ Channel menu skip optimization (no 404 requests)
11. ✅ Settings migration (v1 format with string catalogs)
12. ✅ Dutch-only UI (no language switching in settings)
13. ✅ Account info refresh (background thread, post-login)
14. ✅ Logout confirmation (two-step, My List preservation option)

---

**End of Comprehensive Changes List**
