# Configuration Files

## Pre-generated Reference Files

This directory contains pre-generated configuration files that serve as **reference examples**:

| File | Description |
|------|-------------|
| `data_profile.json` | Database profiling results with column statistics |
| `keys.json` | Primary/foreign key relationship mappings |
| `schema_info.json` | Complete database schema information |
| `schema_info.md` | Human-readable schema documentation |

---

## For Evaluators & First-time Users

These files are provided as **sample references** for the given challenge dataset only. To actually use this product, you must set up your own database with data first.

To get started:

1. **Backup these reference files**:
   ```bash
   mkdir -p backup
   cp *.json *.md backup/
   ```

2. **Follow the setup guide** in [README.md](../../README.md) or [SETUP_GUIDE.md](../../SETUP_GUIDE.md)

By following the setup instructions, you will generate your own configuration files based on your database.