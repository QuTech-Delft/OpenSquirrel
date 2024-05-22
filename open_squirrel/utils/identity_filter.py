from open_squirrel.ir import Gate


def filter_out_identities(l: [Gate]):
    return [g for g in l if not g.is_identity()]
