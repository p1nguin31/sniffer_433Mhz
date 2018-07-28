import logging
import logging.handlers
import __main__ as main
import os.path

my_logger = logging.getLogger(os.path.basename(main.__file__))
my_logger.setLevel(logging.DEBUG)

handler1 = logging.handlers.SysLogHandler(address = ('192.168.1.1',514))
handler = logging.handlers.SysLogHandler(address = '/dev/log', facility=logging.handlers.SysLogHandler.LOG_LOCAL7)

formatter = logging.Formatter(fmt='%(asctime)-15s - [%(name)s] - [%(levelname)s] : %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
handler.setFormatter(formatter)

my_logger.addHandler(handler)
my_logger.addHandler(handler1)

my_logger.info('Starting program')




#logging.basicConfig(level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S',
#                    format='%(asctime)-15s - [%(levelname)s] %(module)s: %(message)s', )

