#!/bin/bash
#SBATCH --partition=short
#SBATCH --nodes=1
#SBATCH --time=8:00:00
#SBATCH --job-name=download_polyhaven_models
#SBATCH --mem=32
#SBATCH --ntasks=8
#SBATCH --output=myjob.download_polyhaven_models.out
#SBATCH --error=myjob.download_polyhaven_models.err

cd /projects/vig/Datasets/Polyhaven
polydown models -f polyhaven_models -s 1k 4k 8k
