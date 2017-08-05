async def get_tags(redis, **identifiers):
    """Deprecated version that requires coming back to python to issue
    every redis command.
    """
    # keys for redis sets represending each identifier e.g. `user:foo`
    identifier_keys = [join(k, v) for k, v in identifiers.items()]

    # a random token to use as a suffix for our 2 temp keys,
    # used to store the results of 2 set union operations.
    token = str(random())

    # the 2 temp keys
    store_pos = join('calculated', 'positive', token)
    store_neg = join('calculated', 'negative', token)

    # temporarily store the result of unioning all members
    # of all 'positive' sets for all identifiers.
    await redis.sunionstore(
        store_pos,
        join(global_type, 'positive'),
        *[join(p, 'positive') for p in identifier_keys])

    # temporarily store the result of unioning all members
    # of all 'negative' sets for all identifiers.
    await redis.sunionstore(
        store_neg,
        join(global_type, 'negative'),
        *[join(p, 'negative') for p in identifier_keys])

    # subtract the negative calculated set from the positive and return.
    result = await redis.sdiff(store_pos, store_neg)

    # delete the temp keys.
    await redis.delete(store_pos, store_neg)

    # return result as a list of `str` objects.
    return [v.decode() for v in result]
