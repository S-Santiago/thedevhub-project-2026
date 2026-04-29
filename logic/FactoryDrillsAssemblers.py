#PERFORADORA
class Drill:
    def __init__(self, coal, groundMaterial, inventory):
        self.coal = coal
        self.groundMaterial = groundMaterial
        self.inventory = inventory

    # Compatibilidad con código antiguo que usa `Coal`
    @property
    def Coal(self):
        return self.coal

    @Coal.setter
    def Coal(self, value):
        self.coal = value

    #consume 1 de carbon y si no hay avisa que falta
    def consume_coal(self, amount=1):
        if self.coal < amount:
            print("No hay suficiente carbon")
            return False
        self.coal -= amount
        return True

    # Alias legacy
    def consumeCoal(self, amount=1):
        return self.consume_coal(amount)


#Perforadora de carbon
class coalDrill(Drill):
    output_kind = "COAL"
    output_amount = 5

    def produce(self, inventory=None):
        target_inventory = inventory if inventory is not None else self.inventory

        if self.groundMaterial != self.output_kind:
            print("La perforadora no esta sobre carbon")
            return 0

        #si no hay carbon no produce
        if not self.consume_coal():
            return 0

        #si hay carbon produce 5 de carbon
        target_inventory.COAL += self.output_amount
        print("En el almacen hay " + str(target_inventory.COAL) + " de carbon")
        return self.output_amount

    # Alias para compatibilidad con versiones anteriores
    def producir(self, inventory=None):
        return self.produce(inventory)


#Perforadora de hierro
class ironDrill(Drill):
    output_kind = "IRON"
    output_amount = 1

    def produce(self, inventory=None):
        target_inventory = inventory if inventory is not None else self.inventory

        if self.groundMaterial != self.output_kind:
            print("La perforadora no esta sobre hierro")
            return 0

        #si no hay carbon no produce
        if not self.consume_coal():
            return 0

        #si hay carbon produce 1 de hierro
        target_inventory.IRON += self.output_amount
        print("En el almacen hay " + str(target_inventory.IRON) + " de hierro")
        return self.output_amount


#Perforadora de cobre
class copperDrill(Drill):
    output_kind = "COPPER"
    output_amount = 2

    def produce(self, inventory=None):
        target_inventory = inventory if inventory is not None else self.inventory

        if self.groundMaterial != self.output_kind:
            print("La perforadora no esta sobre cobre")
            return 0

        #si no hay carbon no produce
        if not self.consume_coal():
            return 0

        #si hay carbon produce 2 de cobre
        target_inventory.COPPER += self.output_amount
        print("En el almacen hay " + str(target_inventory.COPPER) + " de cobre")
        return self.output_amount



#Inventario
class Inventory:
    def __init__(self):
        self.IRON = 0
        self.COPPER = 0
        self.COAL = 0

        self.IRON_PLATE = 0
        self.COPPER_PLATE = 0
        self.COPPER_WIRE = 0



#ENSAMBLADORA
class Assembler:
    def __init__(self, coal, inventory):
        self.coal = coal
        self.inventory = inventory

    # Compatibilidad con código antiguo que usa `Coal`
    @property
    def Coal(self):
        return self.coal

    @Coal.setter
    def Coal(self, value):
        self.coal = value

    #consume 1 de carbon y si no hay avisa que falta
    def consume_coal(self, amount=1):
        if self.coal < amount:
            print("No hay suficiente carbon")
            return False
        self.coal -= amount
        return True

    # Alias legacy
    def consumeCoal(self, amount=1):
        return self.consume_coal(amount)


#Ensambadora de Placa de hierro
class ironPlateAssembler(Assembler):
    output_kind = "IRON_PLATE"
    output_amount = 1

    def produce(self, inventory=None):
        target_inventory = inventory if inventory is not None else self.inventory

        if target_inventory.IRON < 2:
            print("No hay suficiente hierro para producir una placa de hierro")
            return 0

        #si no hay carbon no produce
        if not self.consume_coal():
            return 0

        #si hay carbon produce 1 de placa de hierro
        target_inventory.IRON -= 2
        target_inventory.IRON_PLATE += self.output_amount
        print("En el almacen hay " + str(target_inventory.IRON_PLATE) + " de placa de hierro")
        return self.output_amount


#Ensambadora de Placa de cobre
class copperPlateAssembler(Assembler):
    output_kind = "COPPER_PLATE"
    output_amount = 1

    def produce(self, inventory=None):
        target_inventory = inventory if inventory is not None else self.inventory

        if target_inventory.COPPER < 2:
            print("No hay suficiente cobre para producir una placa de cobre")
            return 0

        #si no hay carbon no produce
        if not self.consume_coal():
            return 0

        #si hay carbon produce 1 de placa de cobre
        target_inventory.COPPER -= 2
        target_inventory.COPPER_PLATE += self.output_amount
        print("En el almacen hay " + str(target_inventory.COPPER_PLATE) + " de placa de cobre")
        return self.output_amount


#Ensambadora de Hilo de cobre
class copperWireAssembler(Assembler):
    output_kind = "COPPER_WIRE"
    output_amount = 1

    def produce(self, inventory=None):
        target_inventory = inventory if inventory is not None else self.inventory

        if target_inventory.COPPER < 1:
            print("No hay suficiente cobre para producir un hilo de cobre")
            return 0

        #si no hay carbon no produce
        if not self.consume_coal():
            return 0

        #si hay carbon produce 1 de hilo de cobre
        target_inventory.COPPER -= 1
        target_inventory.COPPER_WIRE += self.output_amount
        print("En el almacen hay " + str(target_inventory.COPPER_WIRE) + " de hilo de cobre")
        return self.output_amount
