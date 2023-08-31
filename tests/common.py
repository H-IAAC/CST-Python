from multiprocessing import Queue

from cst_python import Codelet, MemoryObject


class PrintMessageCodelet(Codelet):

    def __init__(self, print_queue:Queue) -> None:
        super().__init__()

        self._print_queue = print_queue

        self._trigger : MemoryObject = None
        self._msg : MemoryObject = None


    def proc(self) -> None:
        if self._trigger.get_info():
            msg = self._msg.get_info()
            print(msg)
            self._print_queue.put(msg)
            self._trigger.set_info(False)

    def access_memory_objects(self) -> None:
        self._trigger = self.get_input("trigger")
        self._msg = self.get_output("message")
    
    def calculate_activation(self) -> None:
        pass


class ChangeMessageCodelet(Codelet):

    def __init__(self, new_msg:str) -> None:
        super().__init__()

        self._new_msg = new_msg

        self._trigger : MemoryObject = None
        self._msg : MemoryObject = None

        self._changed = False

    def proc(self) -> None:
        if not self._changed:
            self._trigger.set_info(True)
            self._msg.set_info(self._new_msg)

            self._changed = True

    def access_memory_objects(self) -> None:
        self._trigger = self.get_output("trigger")
        self._msg = self.get_output("message")
    
    def calculate_activation(self) -> None:
        pass
