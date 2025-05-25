import reflex as rx
import time
import json
from pathlib import Path
from savienojums import get_augsnes_mitrums, get_dht22, ieslegt_pumpi

# Iestatijumu fails. Šeit saglabājās vērtības no iestatījumu sadaļas
IESTATIJUMU_FAILS = Path.home() / "Documents" / "bakalaurs_arduino" / "iestatijumi.json"

# Galvenā lietotnes klase. Šeit atrodas visa fona loģika sistēmai
class State(rx.State):
    augsnes_mitrums: float  = 0
    temperatura: float      = 0
    mitrums: float          = 0
    status: str             = "Gaida"
    iestatijumu_status: str = ""
    mitruma_slieksnis: int  = 0
    pumpja_ilgums: int      = 0

    # iestatījumu saglabāšanas funkcija. Saglabā tos IESTATIJUMU_FAILS definētajā failā
    def saglabat_iestatijumus(self):
        iestatijumi = {
            "mitruma_slieksnis": self.mitruma_slieksnis,
            "pumpja_ilgums": self.pumpja_ilgums
        }
        try:
            with open(IESTATIJUMU_FAILS, "w") as f:
                json.dump(iestatijumi, f, indent=4)
            self.iestatijumu_status = "Iestatījumi saglabāti"
        except Exception as e:
            print(f"Kļūda saglabājot iestatījumus: {e}")
            self.iestatijumu_status = "Kļūda saglabājot"

    # Ielādē iestatījumus no faila
    def ieladet_iestatijumus(self):
        if IESTATIJUMU_FAILS.exists():
            try:
                with open(IESTATIJUMU_FAILS, "r") as f:
                    iestatijumi = json.load(f)
                    self.mitruma_slieksnis = iestatijumi.get("mitruma_slieksnis", 40)
                    self.pumpja_ilgums = iestatijumi.get("pumpja_ilgums", 5)
            except Exception as e:
                print(f"Kļūda ielādējot iestatījumus: {e}")

    # Funkcija kas notīra statusa uzrakstu iestatījumu skatā
    def notirit_iestatijumu_status(self):
        self.iestatijumu_status = ""

    # Funkcija sensoru datu atjaunošanai. Atjauno temperatūras un augsnes mitruma sensorus
    def update_sensor(self):
        self.status = "Pārbauda mitrumu"
        self.augsnes_mitrums = get_augsnes_mitrums()
        self.update_dht_data()
        if self.augsnes_mitrums < self.mitruma_slieksnis and self.augsnes_mitrums != -1:
            self.status = "Laista"
            ieslegt_pumpi(True)
            time.sleep(self.pumpja_ilgums)
            ieslegt_pumpi(False)        
        elif self.augsnes_mitrums != -1:
            self.status = "Zeme ir mitra"
        else:
            self.status = "Sensora kļūda"

    # Funkcija DHT22 sensora datu ieguvei
    def update_dht_data(self):
        dht_data = get_dht22()
        self.temperatura = dht_data.get("GT") or 0
        self.mitrums = dht_data.get("GM") or 0

    # setter funkcija mitruma slieksnim
    def set_mitruma_slieksnis(self, val: str):
        self.mitruma_slieksnis = int(val)

    # setter funkcija pumpja ilgumam (sekundēs)
    def set_pumpja_ilgums(self, val: str):
        self.pumpja_ilgums = int(val)

    # laistīšanas funkcija. Ieslēdz pumpi uz iestatījumos norādīto laiku
    def laistisana(self):
        self.status = "Laistīšana sākta (manuāli)"
        ieslegt_pumpi(True)
        time.sleep(self.pumpja_ilgums)
        ieslegt_pumpi(False)
        self.status = "Laistīšana pabeigta"

# Reflex navigācija. Tiek definēta sākumlapa un iestatījumu lapa.
def nav() -> rx.Component:
    return rx.hstack(
        rx.link("Sākums", href="/", padding="4", font_weight="bold", color="orange", size="5"),
        rx.link("Iestatījumi", href="/settings", padding="4", font_weight="bold", color="orange", size="5"),
        spacing="8",
        padding="8",
        bg="gray.200",
        width="100%",
        justify="center",
        align="end",
        height="7vh",
    )

# Sākumlapas definīcija
def index() -> rx.Component:
    return rx.vstack(
        nav(),
        rx.center(
            rx.vstack(
                rx.heading("Augsnes mitruma sensors", size="5"),
                rx.card(
                    rx.hstack(
                        rx.vstack(
                            rx.text("Augsnes mistrums: ", size="4", weight="bold"),
                            rx.text(f"Statuss: {State.status}", size="2"),
                        ),
                        rx.vstack(
                            rx.flex(
                                rx.text(f"{State.augsnes_mitrums}%", size="5", color="white"),
                                direction="column",
                                spacing="3",
                                align="center",
                                justify="center",
                                height="7vh",
                                width="10vh",
                            ),
                        ),
                    ),
                    shadow="md",
                    padding="5",
                    border_radius="xl",
                    bg="gray",
                    width="300px"
                ),
                rx.card(
                    rx.vstack(
                        rx.text("Temperatūra un Mitrums", size="4", weight="bold"),
                        rx.text(f"Temperatūra: {State.temperatura}°C", size="3", color="white"),
                        rx.text(f"Mitrums: {State.mitrums}%", size="3", color="white"),
                    ),
                    shadow="md",
                    padding="5",
                    border_radius="xl",
                    bg="gray",
                    width="300px"
                ),
                rx.hstack(
                    rx.button("Pārbaudīt", on_click=State.update_sensor, size="3", color_scheme="orange"), # Sensoru pārbaudes poga. Pie nospiešanas atjauno sensoru datus
                    rx.button("Aplaistīt", on_click=State.laistisana, size="3", color_scheme="blue"), # Manuālā laistīšanas poga. Pie nospiešanas darbina ūdens pumpi
                ),
                rx.moment(interval=60000, on_change=State.update_sensor, display="none"), # Automātiski atjauno sensoru datus katru minūti
                rx.moment(on_mount=State.ieladet_iestatijumus, display="none"), # Pie ielādes, ielādē iestatījumus no faila
                spacing="5",
                padding="6",
                align="center",
            ),
            width="100vw",
            min_height="100vh",
            bg="gray.100",
        )
    )

# Iestatījumu lapas definīcija
def settings() -> rx.Component:
    return rx.vstack(
        nav(),
        rx.center(
            rx.vstack(
                rx.moment(on_mount=State.ieladet_iestatijumus, display="none"), # Ielādējot lapu ielādē iestatījumus
                rx.heading("Iestatījumi", size="5"),
                rx.hstack(
                    rx.text("Mitruma slieksnis (%):"),
                    rx.input(
                        type_="number",
                        value=State.mitruma_slieksnis,
                        on_change=State.set_mitruma_slieksnis,
                    ),
                ),
                rx.hstack(
                    rx.text("Laistīšanas ilgums (sek):"),
                    rx.input(
                        type_="number",
                        value=State.pumpja_ilgums,
                        on_change=State.set_pumpja_ilgums,
                    ),
                ),
                rx.button("Saglabāt iestatījumus", on_click=State.saglabat_iestatijumus, color_scheme="green"), # Iestatījumu saglabāšanas poga. Pie nospiešanas saglabā
                rx.text(State.iestatijumu_status, size="2", color="gray"),
                rx.moment(interval=6000, on_change=State.notirit_iestatijumu_status, display="none"),
                spacing="4",
                padding="6",
            ),
            width="100vw",
            min_height="100vh",
            bg="gray.100",
        )
    )

# Sistēmai pievienotas iepriekš definētās lapas
app = rx.App()
app.add_page(index, title="Augsnes sensors")
app.add_page(settings, title="Iestatījumi")
