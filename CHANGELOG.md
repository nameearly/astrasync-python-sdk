# Changelog

All notable changes to the AstraSync Python SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-10-15

### 🎉 Production Release

This marks the official production release of the AstraSync Python SDK!

### Changed
- **BREAKING**: Updated API endpoint from Railway development environment to production (`https://astrasync.ai/api/v1`)
- Updated all documentation from "Developer Preview" to "Production"
- Removed trust score cap (was limited to 95 for preview, now supports full 100 scale)
- Updated development status from "Alpha" to "Production/Stable"
- Updated SDK version in User-Agent headers to 1.0.0
- Updated all code examples to reflect production environment

### Improved
- Trust score calculations now support full 0-100 range
- Production-grade API endpoints with improved reliability
- Enhanced documentation for production use

### Migration Guide

If you're upgrading from v0.2.x (Developer Preview):

1. **Update your installation:**
   ```bash
   pip install --upgrade git+https://github.com/AstraSyncAI/astrasync-python-sdk.git
   ```

2. **No code changes required** - The SDK is backward compatible. All API calls will automatically use the new production endpoints.

3. **Agent IDs:** New registrations will receive production `ASTRAS-XXX` IDs instead of temporary `TEMP-XXX` IDs.

4. **Trust Scores:** Trust scores are now calculated on the full 0-100 scale instead of capped at 95.

### Note
- Blockchain integration remains in progress and will be fully enabled in a future release
- All existing functionality continues to work as expected

---

## [0.2.5] - 2025-09-XX

### Developer Preview Release
- Initial public release
- Support for 17+ agent frameworks
- Auto-detection of agent types
- Basic trust scoring (capped at 95)
- Railway development API endpoint

