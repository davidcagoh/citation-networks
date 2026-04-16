% function r = doi2date(doi)
% a script to collect publication dates from doi
% 
% Nikos Pitsianis
% Sept 30, 2024

clear

mf = matfile('../data/aps-2020-author-doi-citation.mat');

doi = mf.doi;
pubDate = strings(length(doi),1);

%% Collect dates from the metadata stored locally

jsondatadir = '~/Downloads/aps-dataset-metadata-2020';
jsonfiles = dir(sprintf('%s/*/*/*.json', jsondatadir));

%% init
n = length(jsonfiles);
adoi = strings(n,1);
adate = strings(n,1);

%% do it
for i = 1:length(jsonfiles)
  jsonfile = sprintf('%s/%s', jsonfiles(i).folder, jsonfiles(i).name);
  articleinfo = jsondecode(fileread(jsonfile));
  adoi(i) = articleinfo.id;
  if isfield(articleinfo, 'date')
    r = articleinfo.date;
    if rem(i,100000) == 0
      fprintf('doi(%d) = %s, date = %s\n', i, articleinfo.id, r)
    end
    adate(i) = r;
  else
    fprintf('Date field not found for doi(%d) = %s\n', i, articleinfo.id)
  end
end

%% match the two lists of dois
[~,ia,ib] = intersect(doi, adoi);
pubDate(ia) = adate(ib);

%% save the results

save('../data/aps-2020-author-doi-citation.mat', 'pubDate', '-append')

%% identify articles per decade


return

%% Collect publication dates

baseurl = 'https://api.crossref.org/works/';

for i = 1:1000 % length(doi)
  url = sprintf('%s%s', baseurl, doi(i));

  % try
    response = webread(url,'Timeout',10);
    if isfield(response.message, 'published')
      r = response.message.published.date_parts;
      pubDate(i,:) = r;
      fprintf('doi(%d) = %s, date = %d-%d-%d\n', i, doi(i), r(1), r(2), r(3))
    else
      % error('Date field not found')
      % keyboard
      fprintf('Date field not found for doi(%d) = %s\n', i, doi(i))
    end
  % catch
    % do something smart
  %  keyboard
  %end
  pause(0.1)
end

