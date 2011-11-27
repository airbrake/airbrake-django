from decorator import decorator
from multiprocessing import Process


@decorator
def async(f, *args, **kwargs):
    p = Process(target=f, args=args, kwargs=kwargs)
    p.start()
