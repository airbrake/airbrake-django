try:
    from djutils.decorators import async
except ImportError:
    from threading import Thread

    def async(f):
        def __inner__(*args, **kwargs):
            thread = Thread(target=f, args=args, kwargs=kwargs)
            thread.start()
