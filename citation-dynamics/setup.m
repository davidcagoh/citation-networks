%% setup.m
% Add all relevant folders to MATLAB path and set canonical data paths

% Add source and utility code
addpath(genpath(fullfile(pwd, 'src')));
addpath(genpath(fullfile(pwd, 'utils')));
addpath(genpath(fullfile(pwd, 'deps')));

% Data directories
DATA_RAW = fullfile(pwd, 'data', 'raw');         % optional: full JSON archive
DATA_PROCESSED = fullfile(pwd, 'data', 'processed'); % canonical MAT/CSV
DATA_SAMPLE = fullfile(pwd, 'data', 'sample');   % small test datasets

% Optional: experiments output folder
EXPERIMENTS_DIR = fullfile(pwd, 'experiments');

% Save paths in base workspace for scripts
assignin('base', 'DATA_RAW', DATA_RAW);
assignin('base', 'DATA_PROCESSED', DATA_PROCESSED);
assignin('base', 'DATA_SAMPLE', DATA_SAMPLE);
assignin('base', 'EXPERIMENTS_DIR', EXPERIMENTS_DIR);

fprintf('MATLAB paths set. DATA_PROCESSED = %s\n', DATA_PROCESSED);