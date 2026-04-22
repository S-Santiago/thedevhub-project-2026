#PERFORADORA
class Drill:
    def __init__(self, coal, groundMaterial, inventory):
        self.Coal = coal
        self.groundMaterial = groundMaterial
        self.inventory = inventory

    #consume 1 de carbon y si no hay avisa que falta
    def consumeCoal(self, amount=1):
        if self.Coal < amount:
            print("No hay suficiente carbon")
            return False
        self.Coal -= amount
        return True


#Perforadora de carbon
class coalDrill(Drill):
    output_kind = "COAL"
    output_amount = 5

    def producir(self, inventory):
        if self.groundMaterial != "COAL":
            print("La perforadora no esta sobre carbon")
            return 0

        #si no hay carbon no produce
        if not self.consumeCoal():
            return 0

        #si hay carbon produce 5 de carbon
        self.inventory.COAL += self.output_amount
        print("En el almacen hay " + str(self.inventory.COAL) + " de carbon")
        return self.output_amount


#Perforadora de hierro
class ironDrill(Drill):
    output_kind = "IRON"
    output_amount = 1

    def produce(self, inventory):
        if self.groundMaterial != "IRON":
            print("La perforadora no esta sobre hierro")
            return 0

        #si no hay carbon no produce
        if not self.consumeCoal():
            return 0

        #si hay carbon produce 1 de hierro
        self.inventory.IRON += self.output_amount
        print("En el almacen hay " + str(self.inventory.IRON) + " de hierro")
        return self.output_amount


#Perforadora de cobre
class copperDrill(Drill):
    output_kind = "COPPER"
    output_amount = 2

    def produce(self, inventory):
        if self.groundMaterial != "COPPER":
            print("La perforadora no esta sobre cobre")
            return 0

        #si no hay carbon no produce
        if not self.consumeCoal():
            return 0

        #si hay carbon produce 2 de cobre
        self.inventory.COPPER += self.output_amount
        print("En el almacen hay " + str(self.inventory.COPPER) + " de cobre")
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

    #consume 1 de carbon y si no hay avisa que falta
    def consumeCoal(self, amount=1):
        if self.coal < amount:
            print("No hay suficiente carbon")
            return False
        self.coal -= amount
        return True


#Ensambadora de Placa de hierro
class ironPlateAssembler(Assembler):
    output_kind = "IRON_PLATE"
    output_amount = 1

    def produce(self, inventory):
        if self.inventory.IRON < 2:
            print("No hay suficiente hierro para producir una placa de hierro")
            return 0

        #si no hay carbon no produce
        if not self.consumeCoal():
            return 0

        #si hay carbon produce 1 de placa de hierro
        self.inventory.IRON -= 2
        self.inventory.IRON_PLATE += self.output_amount
        print("En el almacen hay " + str(self.inventory.IRON_PLATE) + " de placa de hierro")
        return self.output_amount


#Ensambadora de Placa de cobre
class copperPlateAssembler(Assembler):
    output_kind = "COPPER_PLATE"
    output_amount = 1

    def produce(self, inventory):
        if self.inventory.COPPER < 2:
            print("No hay suficiente cobre para producir una placa de cobre")
            return 0

        #si no hay carbon no produce
        if not self.consumeCoal():
            return 0

        #si hay carbon produce 1 de placa de cobre
        self.inventory.COPPER -= 2
        self.inventory.COPPER_PLATE += self.output_amount
        print("En el almacen hay " + str(self.inventory.COPPER_PLATE) + " de placa de cobre")
        return self.output_amount


#Ensambadora de Hilo de cobre
class copperWireAssembler(Assembler):
    output_kind = "COPPER_WIRE"
    output_amount = 1

    def produce(self, inventory):
        if self.inventory.COPPER < 1:
            print("No hay suficiente cobre para producir un hilo de cobre")
            return 0

        #si no hay carbon no produce
        if not self.consumeCoal():
            return 0

        #si hay carbon produce 1 de hilo de cobre
        self.inventory.COPPER -= 1
        self.inventory.COPPER_WIRE += self.output_amount
        print("En el almacen hay " + str(self.inventory.COPPER_WIRE) + " de hilo de cobre")
        return self.output_amount