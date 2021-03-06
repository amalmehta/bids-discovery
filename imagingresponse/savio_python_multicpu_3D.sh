#!/bin/bash

# Remember:
# Submit via: sbatch ...

#SBATCH -J Python

#SBATCH --account=fc_cosi
#SBATCH --partition=savio2
#SBATCH --qos=savio_normal

#SBATCH -t 1:00:00

#SBATCH --ntasks=1
#SBATCH --cpus-per-task=24

#SBATCH --signal=2@60

##SBATCH --mail-user=
##SBATCH --mail-type=ALL


echo "Starting submit on host ${HOST}..."

echo "Loading modules..."
module load gcc/6.3.0 cmake python/3.6 blas cuda tensorflow/1.10.0-py36-pip-cpu


export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK

# Attention: Always use -b for batch mode
python3 -u explore_layouts.py
echo "Done with script"

wait