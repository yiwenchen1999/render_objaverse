# Distributed Rendering Scripts for render_3dmodels_dense_addLights.py

This directory contains scripts for distributed rendering of 3D models with additional lighting using multiple GPU workers.

## 📁 Files Created

1. **`distribute_render_3dmodels_addLights.py`** - Python dispatcher that spawns multiple workers per GPU
2. **`render_3dmodels_addLights_0_50.sh`** - Example SBATCH script for rendering models 0-50
3. **`generate_render_3dmodels_addLights_scripts.sh`** - Generates multiple SBATCH scripts for different ranges
4. **`submit_all_render_3dmodels_addLights.sh`** - Submits all generated scripts at once

## 🚀 Quick Start

### Option 1: Single Job Submission

```bash
cd /projects/vig/yiwenc/ResearchProjects/lightingDiffusion/3dgs/render_objaverse

# Submit a single range (e.g., models 0-50)
sbatch scripts/render_3dmodels_addLights_0_50.sh
```

### Option 2: Generate and Submit Multiple Jobs

```bash
cd /projects/vig/yiwenc/ResearchProjects/lightingDiffusion/3dgs/render_objaverse

# Step 1: Generate SBATCH scripts for multiple ranges
bash scripts/generate_render_3dmodels_addLights_scripts.sh

# Step 2: Submit all generated jobs
bash scripts/submit_all_render_3dmodels_addLights.sh
```

### Option 3: Direct Python Call (for testing)

```bash
cd /projects/vig/yiwenc/ResearchProjects/lightingDiffusion/3dgs/render_objaverse

python scripts/distribute_render_3dmodels_addLights.py \
  --num_gpus 1 \
  --workers_per_gpu 2 \
  --group_start 0 \
  --group_end 10 \
  --num_views 30 \
  --num_test_views 50 \
  --num_white_envs 1 \
  --num_env_lights 0 \
  --num_white_pls 3 \
  --num_rgb_pls 1 \
  --num_combined_lights 0
```

## ⚙️ Configuration

### Lighting Parameters (in SBATCH scripts)

Edit the lighting parameters in the SBATCH scripts to customize:

```bash
--num_white_envs 1        # Number of white environment lights
--num_env_lights 0        # Number of colored environment lights
--num_white_pls 3         # Number of white point lights
--num_rgb_pls 1           # Number of RGB point lights
--num_multi_pls 0         # Number of multi-point light configurations
--num_area_lights 0       # Number of area lights
--num_combined_lights 0   # Number of combined lights (env + point)
```

### Performance Parameters

```bash
--num_gpus 1              # Number of GPUs to use
--workers_per_gpu 2       # Number of concurrent workers per GPU
```

**Note:** More workers = better GPU utilization, but requires more CPU/RAM

### Paths

Modify in the SBATCH scripts if needed:

```bash
--rendered_dir_name rendered_dense_lightPlus  # Output directory name
--csv_path test_obj.csv                        # CSV file with model list
--proj_root /projects/vig/yiwenc/...          # Project root directory
```

## 📊 Monitoring Jobs

### Check job status:
```bash
squeue -u $USER
```

### Check job details:
```bash
scontrol show job <JOB_ID>
```

### View job output:
```bash
tail -f myjob.render_models_addLights_dist_0_50.out
tail -f myjob.render_models_addLights_dist_0_50.err
```

### Cancel jobs:
```bash
scancel <JOB_ID>           # Cancel specific job
scancel -u $USER           # Cancel all your jobs
```

## 📝 Customizing Ranges

To customize the model ranges, edit `generate_render_3dmodels_addLights_scripts.sh`:

```bash
RANGES=(
  "0 50"
  "50 100"
  "100 150"
  # Add more ranges as needed
  "500 550"
)
```

Then regenerate the scripts:
```bash
bash scripts/generate_render_3dmodels_addLights_scripts.sh
```

## 🔧 Troubleshooting

### Issue: GPU out of memory
**Solution:** Reduce `--workers_per_gpu` from 2 to 1

### Issue: Jobs fail silently
**Solution:** Check error logs in `myjob.render_models_addLights_dist_*.err`

### Issue: Slow rendering
**Solution:** 
- Check if models are being skipped (done.txt exists)
- Verify GPU utilization with `nvidia-smi`
- Increase `--workers_per_gpu` if GPU is underutilized

## 📂 Output Structure

Rendered models will be saved to:
```
/projects/vig/Datasets/objaverse/hf-objaverse-v1/rendered_dense_lightPlus/
├── <model_uid>/
│   ├── train/
│   │   ├── cameras.json
│   │   ├── white_env_0/
│   │   ├── white_pl_0/
│   │   ├── rgb_pl_0/
│   │   └── ...
│   ├── test/
│   │   └── (same structure)
│   ├── normalize.json
│   └── done.txt
```

## 🎯 Best Practices

1. **Start small**: Test with a small range (e.g., 0-10) before scaling up
2. **Monitor resources**: Use `sig` and `squeue` to check cluster status
3. **Batch submission**: Don't submit too many jobs at once to avoid overwhelming the scheduler
4. **Clean up**: Remove incomplete renders if jobs fail (look for missing `done.txt`)

## 🔗 Related Scripts

- `render_3dmodels_dense.py` - Basic 3D model rendering (no additional lights)
- `render_3dscenes_dense.py` - 3D scene rendering (with multiple objects)
- `distribute_render_3dscenes.py` - Distributed scene rendering dispatcher
