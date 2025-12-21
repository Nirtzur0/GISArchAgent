# Vector Database Validation & Health Check System

## Overview

The GIS Architecture Agent now includes **comprehensive health monitoring** for the vector database that runs automatically on app startup and can be checked anytime.

## What Gets Validated

### 1. **Initialization Status**
- ✅ Database exists with data
- ✅ Auto-initialization if empty
- Minimum 10 regulations required

### 2. **Data Completeness**
- ⚠️ Warning if < 100 regulations
- ❌ Critical if < 10 regulations
- Recommended: 100+ regulations for production

### 3. **Data Freshness**
- ⚠️ Warning if > 30 days old
- ❌ Critical if > 90 days old
- Tracked via metadata file

### 4. **Data Integrity**
- Checks for corrupted entries
- Validates required fields
- Samples regulations for quality

### 5. **Metadata Consistency**
- Tracks last update timestamp
- Records regulation counts
- Monitors data quality metrics

## When Validation Runs

### Automatic Validation

**1. App Startup (Every Time)**
```python
# In factory.py - get_regulation_repository()
repo = ChromaRegulationRepository()
health_check()  # ← Runs automatically
```

**2. Factory First Access**
- When `get_regulation_repository()` is first called
- Validates health
- Auto-initializes if uninitialized
- Logs status to console

### Manual Validation

**3. Programmatic Check**
```python
from src.infrastructure.factory import get_factory

factory = get_factory()
status = factory.get_vectordb_status()

print(f"Status: {status['status']}")  # healthy, warning, critical, uninitialized
print(f"Total Regulations: {status['total_regulations']}")
print(f"Needs Refresh: {status['needs_refresh']}")
```

**4. Web Interface**
- Data Management page shows health status
- Real-time health monitoring
- Issues and recommendations displayed

## Health Status Levels

### ✅ **HEALTHY**
- Database initialized
- ≥10 regulations
- Data < 30 days old
- No integrity issues

**Actions**: None needed

### ⚠️ **WARNING**
- 10-99 regulations (low count)
- Data 30-90 days old
- No metadata tracking

**Actions**: Consider data refresh

### ❌ **CRITICAL**
- <10 regulations
- Data >90 days old
- Integrity issues detected

**Actions**: **URGENT** - Run data refresh immediately

### ⚪ **UNINITIALIZED**
- No data in database
- Empty collection

**Actions**: Auto-initialization triggered

## Configuration

### Thresholds (Customizable)

Located in `src/vectorstore/health_check.py`:

```python
MIN_REGULATIONS = 10          # Minimum acceptable
RECOMMENDED_REGULATIONS = 100  # Production recommended
MAX_AGE_DAYS = 30             # Warning threshold
CRITICAL_AGE_DAYS = 90        # Critical threshold
```

### Metadata Tracking

File: `data/vectorstore/metadata.json`

```json
{
  "last_updated": "2025-12-22T10:30:00",
  "total_regulations": 10,
  "last_refresh_added": 5,
  "last_check": "2025-12-22T14:15:00"
}
```

## Usage Examples

### Check Health Status

```python
from src.vectorstore.health_check import check_vectordb_health
from src.infrastructure.factory import get_factory

factory = get_factory()
repo = factory.get_regulation_repository()

# Perform health check
result = check_vectordb_health(repo)

if result.is_healthy:
    print(f"✅ Database healthy: {result.stats['total_regulations']} regulations")
else:
    print(f"❌ Issues detected:")
    for issue in result.issues:
        print(f"   - {issue}")
    
    print(f"\n💡 Recommendations:")
    for rec in result.recommendations:
        print(f"   - {rec}")
```

### Update Metadata After Data Refresh

```python
from src.vectorstore.health_check import VectorDBHealthChecker
from src.infrastructure.factory import get_factory

factory = get_factory()
repo = factory.get_regulation_repository()

# Add new regulations...
# ...

# Update metadata
checker = VectorDBHealthChecker(repo)
checker.update_metadata(regulations_added=50)
```

### Get Status Display for UI

```python
from src.vectorstore.health_check import VectorDBHealthChecker
from src.infrastructure.factory import get_factory

factory = get_factory()
repo = factory.get_regulation_repository()

checker = VectorDBHealthChecker(repo)
display_text = checker.get_status_display()

print(display_text)
# Output:
# ✅ Vector Database Status: **HEALTHY**
# 
# 📊 **Statistics:**
# - Total Regulations: 150
# - Last Updated: 5 days ago
```

## Integration Points

### 1. Factory (`src/infrastructure/factory.py`)

```python
def _ensure_vectordb_initialized(self):
    """Enhanced with comprehensive health check"""
    health_result = check_vectordb_health(self._regulation_repository)
    
    if health_result.status == 'critical':
        logger.error("❌ CRITICAL: Database health issues")
        # Show issues and recommendations
    elif health_result.status == 'warning':
        logger.warning("⚠️ WARNING: Database needs attention")
    else:
        logger.info("✅ Database healthy")
```

### 2. Web Interface (Data Management Page)

```python
# Get comprehensive status
status = factory.get_vectordb_status()

# Display health banner
if status['status'] == 'healthy':
    st.success("✅ Database Healthy")
elif status['status'] == 'warning':
    st.warning("⚠️ Database Warning")
    for issue in status['issues']:
        st.warning(f"- {issue}")
```

### 3. Monitoring Scripts

```python
# scripts/check_db_health.py

from src.infrastructure.factory import get_factory

factory = get_factory()
status = factory.get_vectordb_status()

if status['status'] == 'critical':
    send_alert("Database critical!")
    exit(1)
```

## Logging Output

### Startup Logs

**Healthy Database:**
```
✅ Vector database healthy: 150 regulations
   Last updated: 5 days ago
```

**Warning Status:**
```
⚠️ Vector database health: WARNING
   Regulations: 10
   - Low regulation count: 10 (recommended: 100)
   - Unknown data age - no metadata found
   💡 Consider running full data sync
   💡 Run data refresh to track freshness
```

**Critical Status:**
```
❌ Vector database health: CRITICAL
   - Only 5 regulations (minimum: 10)
   - Data critically outdated: 95 days old
   💡 URGENT: Run data refresh immediately
   💡 Fetch more regulations from iPlan
```

## Maintenance Workflow

### Regular Maintenance

1. **Check health** on app startup (automatic)
2. **Review warnings** in logs
3. **Refresh data** if needed (monthly recommended)
4. **Update metadata** after refreshes

### Recommended Schedule

| Action | Frequency |
|--------|-----------|
| Automatic health check | Every app startup |
| Manual inspection | Weekly |
| Data refresh | Monthly |
| Full rebuild | Quarterly |

### Data Refresh Commands

```bash
# Check current status
python -c "from src.infrastructure.factory import get_factory; \
           factory = get_factory(); \
           status = factory.get_vectordb_status(); \
           print(status)"

# Run data refresh (future implementation)
python scripts/refresh_regulations.py

# Rebuild database (use with caution)
python scripts/rebuild_vectordb.py
```

## Benefits

### For Developers
- ✅ Automatic validation on startup
- ✅ Clear logging of issues
- ✅ Programmatic access to health status
- ✅ Customizable thresholds

### For Users
- ✅ Visual health indicators in UI
- ✅ Clear recommendations
- ✅ Data freshness tracking
- ✅ Confidence in data quality

### For Operations
- ✅ Monitoring integration ready
- ✅ Alert triggers available
- ✅ Maintenance scheduling support
- ✅ Health history tracking

## Troubleshooting

### Issue: Health check fails with error

**Check:**
1. Database file exists: `data/vectorstore/chroma.sqlite3`
2. Permissions correct for data directory
3. ChromaDB dependencies installed

### Issue: Always shows "Unknown data age"

**Solution:**
```python
from src.vectorstore.health_check import VectorDBHealthChecker
from src.infrastructure.factory import get_factory

factory = get_factory()
repo = factory.get_regulation_repository()

checker = VectorDBHealthChecker(repo)
checker.update_metadata()  # Creates metadata file
```

### Issue: Status shows "WARNING" but data seems fine

**Check thresholds:**
- Low regulation count (< 100)?
- Data age unknown (no metadata)?
- These are warnings, not errors - system still functional

## Future Enhancements

### Planned Features
- 📊 Health check history tracking
- 📈 Trend analysis (regulation growth over time)
- 🔔 Email/Slack alerts for critical status
- 🔄 Automatic data refresh scheduling
- 📉 Performance metrics tracking
- 🧪 Data quality scoring

### Integration Possibilities
- Prometheus metrics export
- Grafana dashboards
- CI/CD health checks
- Automated testing pipelines

## Summary

The vector database validation system provides:

1. **Automatic validation** on every app startup
2. **Comprehensive health monitoring** (initialization, completeness, freshness, integrity)
3. **Clear status levels** (healthy, warning, critical, uninitialized)
4. **Actionable recommendations** for each issue
5. **Metadata tracking** for data freshness
6. **UI integration** for visual monitoring
7. **Programmatic access** for automation

**Result**: You always know the health of your vector database and what actions to take!
