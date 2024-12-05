# File: x_bank.py

import msvcrt
import os
import random
import hashlib
import json
import time
import threading
import yfinance as yf
from colorama import Fore, Style, init
import pandas as pd
from datetime import datetime, timedelta
import plotext as plt
import numpy as np

init(autoreset=True)  # Ensures color reset after each output


class User:
    def __init__(self, name, surname, password, age, user_id, permissions=1, balance=0, wallet=None, trust=100, loans=None, can_delete=True, code=None,transaction_history=None):
        self.name = name
        self.surname = surname
        self.password = password
        self.age = age
        self.user_id = user_id
        self.permissions = permissions  # 1 for user, 0 for admin
        self.balance = balance
        self.wallet = wallet or {}
        self.loans = loans or {}
        self.can_delete = can_delete
        self.code = code
        self.trust = trust
        self.transaction_history = transaction_history or []

    def check_delete(self):
        return self.balance == 0 and not self.wallet

    def log_transaction(self, description, amount):
        self.transaction_history.append({"description": description, "amount": amount})

    def to_dict(self):
        return vars(self)

    @staticmethod
    def from_dict(data):
        return User(**data)


class Bank:
    def __init__(self, name="X Bank"):
        self.name = name
        self.users = []
        self.load_users()
        self.current_user = None
        self.loan_threads = {}

    def load_users(self):
        if os.path.exists("credentials.json"):
            with open("credentials.json", "r") as file:
                users_data = json.load(file)
                self.users = [User.from_dict(user) for user in users_data]
        else:
            self.users = []

    def save_users(self):
        with open("credentials.json", "w") as file:
            json.dump([user.to_dict() for user in self.users], file, indent=4)

    def clear_screen(self):
        os.system("cls" if os.name == "nt" else "clear")

    def fake_loading_bar(self, text="Loading"):
        print(Fore.LIGHTBLUE_EX + text, end="")
        for _ in range(10):
            print("#", end="", flush=True)
            time.sleep(0.1)
        print()

    def display_logo(self):
        self.clear_screen()
        logo = f"""
        {Fore.LIGHTBLUE_EX}██╗  ██╗    ██████╗  █████╗ ███╗   ██╗██╗  ██╗
        ╚██╗██╔╝    ██╔══██╗██╔══██╗████╗  ██║██║ ██╔╝
         ╚███╔╝     ██████╔╝███████║██╔██╗ ██║█████╔╝ 
         ██╔██╗     ██╔══██╗██╔══██║██║╚██╗██║██╔═██╗ 
        ██╔╝ ██╗    ██████╔╝██║  ██║██║ ╚████║██║  ██╗
        ╚═╝  ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝
                                              
        Welcome to {self.name}!{Style.RESET_ALL}
        """
        print(logo)
        print(Fore.LIGHTBLUE_EX + "-" * 60)

    def main_menu(self):
        while True:
            self.display_logo()
            print(Fore.LIGHTBLUE_EX + "1. Ouvrir un compte")
            print(Fore.LIGHTBLUE_EX + "2. Se connecter")
            print(Fore.LIGHTBLUE_EX + "3. Quitter")
            print(Fore.LIGHTBLUE_EX + "-" * 60)
            choice = input(Fore.LIGHTBLUE_EX + "Choisissez une option: ")
            self.clear_screen()
            if choice == "1":
                self.create_user()
            elif choice == "2":
                self.login()
            elif choice == "3":
                print(Fore.LIGHTBLUE_EX + "Merci de visiter X Bank!")
                break
            else:
                print(Fore.LIGHTBLUE_EX + "Option invalide, veuillez réessayer.")

    def create_user(self):
        self.display_logo()
        print(Fore.LIGHTBLUE_EX + "Création d'un nouveau compte.")
        name = input(Fore.LIGHTBLUE_EX + "Entrez votre nom: ")
        surname = input(Fore.LIGHTBLUE_EX + "Entrez votre prénom: ")
        while True:
            pwd = input(Fore.LIGHTBLUE_EX + "Entrez un mot de passe (6 chiffres): ")
            if len(pwd) == 6 and pwd.isdigit():
                break
            print(Fore.LIGHTBLUE_EX + "Mot de passe invalide! Essayez encore.")
        conf_pwd = input(Fore.LIGHTBLUE_EX + "Confirmez votre mot de passe: ")
        while pwd != conf_pwd:
            print(Fore.LIGHTBLUE_EX + "Les mots de passe ne correspondent pas!")
            conf_pwd = input(Fore.LIGHTBLUE_EX + "Confirmez votre mot de passe: ")
        age = int(input(Fore.LIGHTBLUE_EX + "Entrez votre âge: "))
        if 13 <= age <= 123:
            user_id = name[0] + str(random.randint(1000, 9999)) + surname[-1]
            code = random.randint(1000, 9999)
            hashed_pwd = hashlib.md5(pwd.encode()).hexdigest()
            permissions = 0 if name.lower() == "admin" else 1
            new_user = User(name, surname, hashed_pwd, age, user_id, permissions, code=code)
            self.users.append(new_user)
            self.save_users()
            print(Fore.LIGHTBLUE_EX + f"Compte créé avec succès! Votre ID: {user_id}")
            self.fake_loading_bar("Finalisation")
        else:
            print(Fore.LIGHTBLUE_EX + "Âge non valide! Vous devez avoir entre 13 et 123 ans.")
        msvcrt.getch()

    def login(self):
        self.display_logo()
        print(Fore.LIGHTBLUE_EX + "Connexion.")
        name = input(Fore.LIGHTBLUE_EX + "Entrez votre nom: ")
        surname = input(Fore.LIGHTBLUE_EX + "Entrez votre prénom: ")
        pwd = input(Fore.LIGHTBLUE_EX + "Entrez votre mot de passe: ")
        hashed_pwd = hashlib.md5(pwd.encode()).hexdigest()
        for user in self.users:
            if user.name == name and user.surname == surname and user.password == hashed_pwd:
                self.current_user = user
                self.fake_loading_bar("Connexion en cours")
                if self.current_user.permissions == 0:
                    self.admin_dashboard()
                else:
                    self.user_dashboard()
                return
        print(Fore.LIGHTBLUE_EX + "Identifiants incorrects!")
        msvcrt.getch()

    def admin_dashboard(self):
        while True:
            self.display_logo()
            print(Fore.LIGHTBLUE_EX + f"Bienvenue Admin {self.current_user.name}!")
            print(Fore.LIGHTBLUE_EX + "1. Supprimer un compte")
            print(Fore.LIGHTBLUE_EX + "2. Modifier un solde")
            print(Fore.LIGHTBLUE_EX + "3. Voir les transactions")
            print(Fore.LIGHTBLUE_EX + "4. Quitter")
            choice = input(Fore.LIGHTBLUE_EX + "Choisissez une option: ")
            self.clear_screen()
            if choice == "1":
                self.delete_account()
            elif choice == "2":
                self.modify_balance()
            elif choice == "3":
                self.view_transactions()
            elif choice == "4":
                self.current_user = None
                break
            else:
                print(Fore.LIGHTBLUE_EX + "Option invalide.")

    def delete_account(self):
        user_id = input(Fore.LIGHTBLUE_EX + "Entrez l'ID de l'utilisateur à supprimer: ")
        for user in self.users:
            if user.user_id == user_id:
                if user.permissions == 0:
                    print(Fore.LIGHTBLUE_EX + "Impossible de supprimer un administrateur!")
                    return
                self.users.remove(user)
                self.save_users()
                print(Fore.LIGHTBLUE_EX + f"L'utilisateur {user_id} a été supprimé.")
                return
        print(Fore.LIGHTBLUE_EX + "Utilisateur non trouvé.")

    def modify_balance(self):
        user_id = input(Fore.LIGHTBLUE_EX + "Entrez l'ID de l'utilisateur: ")
        for user in self.users:
            if user.user_id == user_id:
                amount = float(input(Fore.LIGHTBLUE_EX + "Entrez le nouveau solde: "))
                user.balance = amount
                self.save_users()
                print(Fore.LIGHTBLUE_EX + f"Le solde de l'utilisateur {user_id} a été modifié.")
                return
        print(Fore.LIGHTBLUE_EX + "Utilisateur non trouvé.")

    def view_transactions(self):
          # Module to detect key press (Windows only)

        if self.current_user is None:
            print(Fore.LIGHTRED_EX + "Aucun utilisateur connecté.")
            return

        print(Fore.LIGHTBLUE_EX + "Historique des transactions:")
        if not self.current_user.transaction_history:
            print(Fore.LIGHTBLUE_EX + "Aucune transaction trouvée.")
        else:
            for transaction in self.current_user.transaction_history:
                print(Fore.LIGHTBLUE_EX + f"{transaction['description']}: {transaction['amount']}")

        print(Fore.LIGHTBLUE_EX + "Appuyez sur une touche pour continuer...")
        msvcrt.getch()  # Wait for key press

    def user_dashboard(self):
        while True:
            self.display_logo()
            print(Fore.LIGHTBLUE_EX + f"Bienvenue, {self.current_user.name}!")
            print(Fore.LIGHTBLUE_EX + "1. Investir de l'argent")
            print(Fore.LIGHTBLUE_EX + "2. Emprunter de l'argent")
            print(Fore.LIGHTBLUE_EX + "3. Voir l'historique des transactions")
            print(Fore.LIGHTBLUE_EX + "4. Transférer des fonds")
            print(Fore.LIGHTBLUE_EX + "5. Retirer de l'argent")
            print(Fore.LIGHTBLUE_EX + "6. Afficher le solde")
            print(Fore.LIGHTBLUE_EX + "7. Quitter")
            choice = input(Fore.LIGHTBLUE_EX + "Choisissez une option: ")
            self.clear_screen()
            if choice == "1":
                self.invest()
            elif choice == "2":
                self.take_loan()
            elif choice == "3":
                self.view_transactions()
            elif choice == "4":
                self.transfer_funds()
            elif choice == "5":
                self.withdraw_investment()
            elif choice == "6":
                self.show_balance()
            elif choice == "7":
                print(Fore.LIGHTBLUE_EX + "Déconnexion.")
                self.current_user = None
                break
            else:
                print(Fore.LIGHTBLUE_EX + "Option invalide.")

    def show_balance(self):
        print(Fore.LIGHTBLUE_EX + f"Votre solde actuel est de {self.current_user.balance} euros.")

    def fetch_investment_data(self, ticker):
        """Simulate fetching investment data for assets with random closing prices."""
        # Generate random data for 1 year (365 days)
        num_days = 365
        start_date = datetime.today() - timedelta(days=num_days)
        dates = [start_date + timedelta(days=i) for i in range(num_days)]
        closing_prices = [random.uniform(100, 500) for _ in range(num_days)]  # Simulated closing prices
        return list(zip(dates, closing_prices))  # Return pairs of (date, price)

    def plot_investment(self, data, asset):
        """Plot the investment data with color-coding based on price change."""
        # Prepare dates and prices for plotting
        dates = [entry[0].strftime('%d/%m/%Y') for entry in data]
        prices = [entry[1] for entry in data]

        # Color coding logic
        colors = []
        for i in range(1, len(prices)):
            if prices[i] > prices[i - 1]:  # Price is rising
                colors.append("green")
            else:  # Price is lowering
                colors.append("red")

        # Append the first color (no previous data to compare, choose green or red)
        colors = ["green"] + colors

        # Use plotext to plot the data with color coding
        plt.clf()  # Clear previous plot if any

        # Loop through the data points and plot each with the corresponding color
        for i in range(len(prices) - 1):
            plt.plot([dates[i], dates[i + 1]], [prices[i], prices[i + 1]], color=colors[i])

        # Title and axis labels
        plt.title(f"{asset} Closing Prices Over 1 Year")
        plt.xlabel("Date")
        plt.ylabel("Price ($)")

        # Manually adjust xticks labels (plotext automatically handles the x-axis spacing)
        plt.xticks(dates[::30])  # Show only a subset of dates to avoid clutter

        plt.show()

    def invest(self):
        """Investment menu for the user."""
        assets = {
            "Bitcoin": "BTC-USD",
            "Ethereum": "ETH-USD",
            "Apple": "AAPL",
            "Tesla": "TSLA",
            "Microsoft": "MSFT",
            "Google": "GOOG",
            "Alibaba": "BABA",
        }

        print("Options d'investissement:")
        for idx, asset in enumerate(assets, 1):
            print(f"{idx}. {asset}")

        choice = input("Choisissez un actif pour investir: ")
        if choice.isdigit() and 1 <= int(choice) <= len(assets):
            asset = list(assets.keys())[int(choice) - 1]
            ticker = assets[asset]

            print(f"Chargement des données pour {asset}...")
            data = self.fetch_investment_data(ticker)
            if data is None:
                return

            # Option to view the chart
            view_chart = input("Voulez-vous voir un graphique des données? (oui/non): ").lower()
            if view_chart == "oui":
                self.plot_investment(data, asset)

            # Amount to invest
            amount = float(input(f"Combien voulez-vous investir dans {asset}? "))
            if self.current_user.balance >= amount:
                # Simulate number of shares bought based on the first day's closing price
                shares_bought = amount / data[0][1]  # Buy based on first day's closing price
                self.current_user.wallet[asset] = self.current_user.wallet.get(asset, 0) + shares_bought
                self.current_user.balance -= amount
                self.current_user.log_transaction(f"Investi dans {asset}", -amount)
                print(f"Vous avez investi {amount} dans {asset}.")
            else:
                print("Fonds insuffisants!")
        else:
            print("Option invalide!")

    def withdraw_investment(self):
        """Withdraw money from an invested asset."""
        if not self.current_user.wallet:
            print(Fore.LIGHTBLUE_EX + "Aucun investissement trouvé.")
            return

        print(Fore.LIGHTBLUE_EX + "Vos investissements actuels:")
        for idx, (asset, shares) in enumerate(self.current_user.wallet.items(), 1):
            print(Fore.LIGHTBLUE_EX + f"{idx}. {asset}: {shares} parts")

        choice = input(Fore.LIGHTBLUE_EX + "Choisissez un actif pour retirer de l'argent: ")
        if choice.isdigit() and 1 <= int(choice) <= len(self.current_user.wallet):
            asset = list(self.current_user.wallet.keys())[int(choice) - 1]
            shares = self.current_user.wallet[asset]

            price_per_share = self.fetch_investment_data(asset)[-1][1]  # Simulated current price
            current_value = shares * price_per_share

            amount = float(
                input(Fore.LIGHTBLUE_EX + f"Combien voulez-vous retirer de {asset}? (max {current_value}): "))
            if 0 < amount <= current_value:
                shares_to_sell = amount / price_per_share
                self.current_user.wallet[asset] -= shares_to_sell
                if self.current_user.wallet[asset] <= 0:
                    del self.current_user.wallet[asset]  # Remove asset if fully withdrawn
                self.current_user.balance += amount
                self.current_user.log_transaction(f"Retiré de {asset}", amount)
                print(Fore.LIGHTBLUE_EX + f"Vous avez retiré {amount} de {asset}.")
            else:
                print(Fore.LIGHTRED_EX + "Montant invalide!")
        else:
            print(Fore.LIGHTRED_EX + "Option invalide!")
        msvcrt.getch()

    def transfer_funds(self):
        print(Fore.LIGHTBLUE_EX + "Transfert de fonds:")

        # Collecte des informations de l'utilisateur
        sender_name = input(Fore.LIGHTBLUE_EX + "Votre prénom: ")
        sender_surname = input(Fore.LIGHTBLUE_EX + "Votre nom: ")
        receiver_name = input(Fore.LIGHTBLUE_EX + "Prénom du destinataire: ")
        receiver_surname = input(Fore.LIGHTBLUE_EX + "Nom du destinataire: ")
        amount = float(input(Fore.LIGHTBLUE_EX + "Montant à transférer: "))

        # Recherche des utilisateurs
        sender = self.find_user_by_name(sender_name, sender_surname)
        receiver = self.find_user_by_name(receiver_name, receiver_surname)

        # Vérification de la validité des utilisateurs
        if not sender or not receiver:
            print(Fore.RED + "Nom ou prénom de l'expéditeur ou du destinataire invalide.")
            return

        # Vérification des fonds disponibles
        if sender.balance < amount:
            print(Fore.RED + "Fonds insuffisants.")
            return

        # Réalisation du transfert
        sender.balance -= amount
        receiver.balance += amount

        # Enregistrement des transactions
        sender.log_transaction(f"Transfert à {receiver.name} {receiver.surname}", -amount)
        receiver.log_transaction(f"Transfert de {sender.name} {sender.surname}", amount)

        # Sauvegarde des données
        self.save_users()

        # Confirmation du transfert
        print(Fore.GREEN + f"Transfert réussi! {amount} euros transférés de {sender.name} à {receiver.name}.")
        msvcrt.getch()

    def find_user_by_name(self, name, surname):
        for user in self.users:
            if user.name == name and user.surname == surname:
                return user
        return None

    def start_loan_repayment_thread(self, user):
        def repay_loan():
            while True:
                time.sleep(30)  # Simulate one month in 30 seconds for demonstration
                with threading.Lock():  # Thread-safe access to user data
                    if user.loans.get("Prêt", 0) <= 0:
                        print(Fore.LIGHTBLUE_EX + "Le prêt est entièrement remboursé.")
                        user.loans.pop("Prêt", None)
                        self.loan_threads.pop(user.user_id, None)  # Remove thread reference
                        break
                    elif user.balance >= user.loans["mensualite"]:
                        user.balance -= user.loans["mensualite"]
                        user.loans["Prêt"] -= user.loans["mensualite"]
                        user.log_transaction("Remboursement mensuel automatique", -user.loans["mensualite"])
                        self.save_users()
                        print(Fore.LIGHTBLUE_EX +
                              f"Remboursement de {user.loans['mensualite']} effectué. Solde restant: {user.loans['Prêt']:.2f}")
                    else:
                        print(Fore.LIGHTBLUE_EX +
                              "Fonds insuffisants pour effectuer le remboursement mensuel. Dépôt nécessaire.")
                        break

        # Start the repayment thread if not already running
        if user.user_id not in self.loan_threads:
            loan_thread = threading.Thread(target=repay_loan, daemon=True)
            self.loan_threads[user.user_id] = loan_thread
            loan_thread.start()

    def take_loan(self):
        print(Fore.LIGHTBLUE_EX + "Entretien pour un prêt bancaire.")
        # Entretien d'éligibilité
        print(Fore.LIGHTBLUE_EX + "Veuillez répondre à quelques questions pour déterminer votre éligibilité.")
        age = self.current_user.age
        if age < 18:
            print(Fore.LIGHTBLUE_EX + "Désolé, vous devez avoir au moins 18 ans pour demander un prêt.")
            return

        revenu_stable = input(Fore.LIGHTBLUE_EX + "Avez-vous une source de revenus stable? (oui/non): ").lower()
        if revenu_stable != "oui":
            print(Fore.LIGHTBLUE_EX + "Désolé, nous ne pouvons pas approuver un prêt sans une source de revenus stable.")
            return

        print(Fore.LIGHTBLUE_EX + "Vérification de votre score de confiance...")
        time.sleep(1)
        if self.current_user.trust < 50:
            print(Fore.LIGHTBLUE_EX + "Votre score de confiance est trop bas pour demander un prêt.")
            return

        # Détails du prêt
        print(Fore.LIGHTBLUE_EX + "Félicitations, vous êtes éligible pour un prêt!")
        montant_pret = float(input(Fore.LIGHTBLUE_EX + "Entrez le montant du prêt souhaité: "))
        montant_max = self.current_user.trust * 10
        if montant_pret > montant_max:
            print(Fore.LIGHTBLUE_EX + f"Désolé, le montant maximum que vous pouvez emprunter est de {montant_max}.")
            return

        periode_remboursement = int(input(Fore.LIGHTBLUE_EX + "En combien de mois souhaitez-vous rembourser le prêt? (max 12): "))
        if periode_remboursement > 12 or periode_remboursement <= 0:
            print(Fore.LIGHTBLUE_EX + "La période de remboursement doit être entre 1 et 12 mois.")
            return

        mensualite = round(montant_pret / periode_remboursement, 2)
        print(Fore.LIGHTBLUE_EX + f"Votre paiement mensuel sera de {mensualite} pour {periode_remboursement} mois.")

        # Approbation du prêt
        self.current_user.loans["Prêt"] = montant_pret
        self.current_user.loans["mensualite"] = mensualite
        self.current_user.balance += montant_pret
        self.current_user.log_transaction("Prêt reçu", montant_pret)
        print(Fore.LIGHTBLUE_EX + f"Prêt approuvé! {montant_pret} ont été ajoutés à votre compte.")
        self.save_users()

        # Start the repayment process
        self.start_loan_repayment_thread(self.current_user)
        msvcrt.getch()




if __name__ == "__main__":
    bank = Bank()
    bank.main_menu()
