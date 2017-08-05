local token = ARGV[1];

-- generate the name of the 2 temporary sets the will keep the
-- intermediate calculations.
local all_positive_key = 'temp:'..token..':positive';
local all_negative_key = 'temp:'..token..':negative';

-- add 'positive' and 'negative'suffixes to input keys
local positive_keys = {'global:positive'};
local negative_keys = {'global:negative'};
for i = 1, #KEYS
do
    local k = KEYS[i];
    positive_keys[i+1] = k..':positive';
    negative_keys[i+1] = k..':negative';
end;

-- calculate and store the union of all sets in positive keys
redis.call('sunionstore', all_positive_key, unpack(positive_keys));
-- same for negative
redis.call('sunionstore', all_negative_key, unpack(negative_keys));

-- subtract negatives from positives
local result = redis.call('sdiff', all_positive_key, all_negative_key);

-- delete temp keys
redis.call('del', all_positive_key, all_negative_key)

return result;
