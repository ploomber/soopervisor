#!/bin/bash
#SBATCH --job-name={{name}}
#SBATCH --output=result.out
#

# add any preparation commands here,
# for example, to activate a virtual environment

# keep the command placeholder, it's used internally
srun {{command}}
