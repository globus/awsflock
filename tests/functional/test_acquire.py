def test_acquire_solo(with_table, run_cmd):
    # just acquire the lock and make sure that works (or at least doesn't
    # error)
    run_cmd("awsflock acquire FooLock")
