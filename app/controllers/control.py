from app.view.views import View
from datetime import datetime
from app.view.userviews import UserView
from app.view.clientview import ClientView
from app.view.contractview import ContractView
from app.view.eventview import EventView
import sentry_sdk

class Controler:

    def __init__(self, user, userDAO):
        self.view = View()
        self.userview = UserView()
        self.clientview = ClientView()
        self.contractview = ContractView()
        self.eventview = EventView()
        self.userDAO = userDAO
        self.user = user

    def run(self):
        text = self.userDAO.get_text(1)
        self.view.logtrue(self.user, text.data)
        self.gestboucle()

    def gestboucle(self):
        """
        Gère le menu principal et les choix de 
        l'utilisateur pour la redirection adaptée.
        """
        choix = None
        while choix != "QUIT":
            choix = self.view.menuprincipalgestion(self.user)
            match choix:
                case "US":
                    choix = self.boucleUser()
                case "CL":
                    self.boucleClient()
                case "CO":
                    self.boucleContracts()
                case "EV":
                    self.boucleEvents()
                case "MO":
                    if self.user.authorisation("Gestion"):
                        data = self.view.getText(self.user)
                        self.userDAO.update_text(1, data)
                    else:
                        self.view.notautorized(self.user)
                case "SU":
                    if self.user.authorisation("Gestion"):
                        self.boucleAttributions()
                    else:
                        self.view.notautorized(self.user)

    def boucleAttributions(self):
        """
        Gère la partie de l'appli réservé aux gestionnaire
        Elle permet l'attribution des dossiers et des clients.
        """
        choix = None
        while choix not in ['RET', 'QUIT']:
            companys = self.userDAO.get_all_company_without_user()
            events = self.userDAO.get_all_events_without_user()
            choix = self.userview.logWithoutUser(self.user, events, companys)
            if choix.startswith("AE"):
                id = choix[2:]
                event = self.userDAO.get_event(id)
                users = self.userDAO.get_user_by_role(4)
                user_id = self.userview.chooseUser(users)
                self.userDAO.update_event(event.id, event.event_date_start,
                                          event.event_date_end, event.location,
                                          user_id, event.attendees,
                                          event.notes)
                return 'LIST'
            elif choix.startswith("AC"):
                id = choix[2:]
                company = self.userDAO.get_company(id)
                users = self.userDAO.get_user_by_role(3)
                user_id = self.userview.chooseUser(users)
                self.userDAO.update_company(company.id, company.company_name,
                                            company.address, user_id)
                return 'LIST'
            elif choix == ("QUIT"):
                quit()
            else:
                return 'LIST'

    def boucleUser(self):
        """
        Gère la partie de l'appli réservé aux gestionnaire et admins
        Elle permet la gestion des users.
        
        """
        if (
            self.user.authorisation('Admin') or
            self.user.authorisation('Gestion')
        ):
            choix = None
            while choix not in ['RET', 'QUIT']:
                users = self.userDAO.get_all_user_with_role_name()
                choix = self.userview.logutilisateurs(self.user, users)
                self.main_choice(choix)
        else:
            self.view.notautorized(self.user)

    def main_choice(self, choix):
        """
        Gère la partie le choix de l'utilisateur pour 
        proposer la bonne redirection
        """
        match choix:
            case 'CR':
                self.create_user()
            case _ if choix.startswith("A"):
                id = choix[1:]
                self.handle_user_modification(id)
            case _ if choix.startswith("M"):
                id = choix[1:]
                self.handle_user_modification(id)
            case _ if choix.startswith("S"):
                id = choix[1:]
                self.userDAO.delete_user(id)
            case "QUIT":
                quit()

    def create_user(self):
        """
        Récupère les données de la view pour la création d'un user
        Puis fait appel a la fonction add dédiée du DAO
        """
        nom, email, mot_de_passe, role = self.userview.createuserview()
        self.userDAO.add_user(nom, email, mot_de_passe, int(role))

    def handle_user_modification(self, id):
        choix = None
        while choix not in ['LIST', 'RET', 'QUIT', 'SUPPRIMER']:
            affiche = self.userDAO.get_user(id)
            choix = self.userview.soloUserView(self.user, affiche)
            new_data = choix[3:]
            match choix:
                case "SUPPRIMER":
                    self.userDAO.delete_user(affiche.id)
                case _ if choix.startswith("NO "):
                    self.userDAO.update_user(affiche.id, new_data,
                                             affiche.email, affiche.role_id)
                case _ if choix.startswith("RE "):
                    self.userDAO.update_pasword_user(affiche.id, new_data)
                case _ if choix.startswith("EM "):
                    self.userDAO.update_user(affiche.id, affiche.nom,
                                             new_data, affiche.role_id)
                case "SE AD":
                    self.userDAO.update_user(affiche.id, affiche.nom,
                                             affiche.email, 1)
                case "SE VE":
                    self.userDAO.update_user(affiche.id, affiche.nom,
                                             affiche.email, 3)
                case "SE GE":
                    self.userDAO.update_user(affiche.id, affiche.nom,
                                             affiche.email, 2)
                case "SE SU":
                    self.userDAO.update_user(affiche.id, affiche.nom,
                                             affiche.email, 4)
                case "QUIT":
                    quit()
                case _:
                    print("commande inconnue")

    def boucleClient(self):
        """
        Boucle secondaire
        Elle permet la gestion des clients.
        
        """
        if (
            self.user.authorisation('Admin') or
            self.user.authorisation('Gestion') or
            self.user.authorisation('Sale') or
            self.user.authorisation('Support')
        ):
            choix = None
            while choix not in ['RET', 'QUIT']:
                companys = self.userDAO.get_all_company()
                choix = self.clientview.logclients(self.user, companys)
                self.client_main_choice(choix)
        else:
            self.view.notautorized(self.user)

    def client_main_choice(self, choix):
        """
        Gère la partie le choix de l'utilisateur pour 
        proposer la bonne redirection
        """
        match choix:
            case 'CR':
                self.create_company()
            case _ if choix.startswith("A"):
                id = choix[1:]
                self.handle_company_modification(id)
            case _ if choix.startswith("M"):
                id = choix[1:]
                self.handle_company_modification(id)
            case _ if choix.startswith("S"):
                id = choix[1:]
                self.delete_company(self.userDAO.get_company(id),
                                    self.userDAO.get_all_contact_by_company_id(
                                        id))
                return 'LIST'
            case "QUIT":
                quit()

    def create_company(self):
        """
        Récupère les données de la view pour la création d'une entreprise
        Puis fait appel a la fonction add dédiée du DAO
        """
        compagny_name, adress = self.clientview.createcompany(self.user)
        self.userDAO.add_company(compagny_name, self.user.id, adress)

    def handle_company_modification(self, id):
        choix = None
        while choix not in ['LIST', 'RET', 'QUIT', 'SUPPRIMER']:
            company = self.userDAO.get_company(id)
            contacts = self.userDAO.get_all_contact_by_company_id(id)
            choix = self.clientview.totalViewCompagny(self.user,
                                                      company, contacts)
            self.process_company_modification_choice(choix, company, contacts)

    def process_company_modification_choice(self, choix, company, contacts):
        """
        Gère la partie le choix de l'utilisateur pour 
        proposer la bonne redirection
        """
        match choix:
            case 'CR':
                self.create_contact(company)
            case 'RECUPERER':
                self.recover_company(company)
            case 'SUPPRIMER':
                self.delete_company(company, contacts)
            case _ if choix.startswith("MN "):
                new_data = choix[3:]
                self.update_company_name(company, new_data)
            case _ if choix.startswith("MA "):
                new_data = choix[3:]
                self.update_company_address(company, new_data)
            case _ if choix.startswith("A"):
                id_contact = choix[1:]
                self.handle_contact_modification(id_contact, company)
            case "QUIT":
                quit()
            case _:
                print("commande inconnue")

    def create_contact(self, company):
        """
        Récupère les données de la view pour la création d'un contact
        Puis fait appel a la fonction add dédiée du DAO
        """
        if self.user.authorisation('Sale') and self.user.id == company.user_id:
            name, email, phone, signatory = self.clientview.createcontact(
                company,
                self.user)
            self.userDAO.add_contact(company.id, name, email, phone, signatory)
        else:
            self.view.notautorized(self.user)

    def recover_company(self, company):
        self.userDAO.update_company(company.id, company.company_name,
                                    company.address, self.user.id)

    def delete_company(self, company, contacts):
        if self.user.authorisation('Sale') and self.user.id == company.user_id:
            if contacts:
                for element in contacts:
                    self.userDAO.delete_contact(element.id)
            self.userDAO.delete_company(company.id)
        else:
            self.view.notautorized(self.user)

    def update_company_name(self, company, new_data):
        if self.user.authorisation('Sale') and self.user.id == company.user_id:
            self.userDAO.update_company(company.id, new_data, company.address,
                                        company.user_id)
        else:
            self.view.notautorized(self.user)

    def update_company_address(self, company, new_data):
        if self.user.authorisation('Sale') and self.user.id == company.user_id:
            self.userDAO.update_company(company.id, company.company_name,
                                        new_data, company.user_id)
        else:
            self.view.notautorized(self.user)

    def handle_contact_modification(self, id_contact, company):
        choix = None
        while choix not in ['ENTR', 'RET', 'QUIT', 'SUPPRIMER']:
            contact = self.userDAO.get_contact(id_contact)
            choix = self.clientview.detailedContact(contact, company)
            self.process_contact_modification_choice(choix, contact, company)

    def process_contact_modification_choice(self, choix, contact, company):
        """
        Gère la partie le choix de l'utilisateur pour 
        proposer la bonne redirection
        """
        new_data = choix[3:]
        print(new_data)

        match choix:
            case "SUPPRIMER":
                self.userDAO.delete_contact(contact.id)
            case _ if choix.startswith("NO "):
                self.userDAO.update_contact(contact.id, company.id, new_data,
                                            contact.email, contact.phone,
                                            contact.signatory)
            case _ if choix.startswith("EM "):
                self.userDAO.update_contact(contact.id, company.id,
                                            contact.name, new_data,
                                            contact.phone, contact.signatory)
            case _ if choix.startswith("TE "):
                self.userDAO.update_contact(contact.id, company.id,
                                            contact.name, contact.email,
                                            new_data, contact.signatory)
            case "SI Oui":
                self.userDAO.update_contact(contact.id, company.id,
                                            contact.name, contact.email,
                                            contact.phone, 1)
            case "SI Non":
                self.userDAO.update_contact(contact.id, company.id,
                                            contact.name, contact.email,
                                            contact.phone, 0)
            case "QUIT":
                quit()
            case _:
                print("commande inconnue")

    def boucleContracts(self):
        """
        Boucle secondaire
        Elle permet la gestion des contrats.
        
        """
        if (
            self.user.authorisation('Admin') or
            self.user.authorisation('Gestion') or
            self.user.authorisation('Sale') or
            self.user.authorisation('Support')
        ):
            choix = None
            while choix not in ['RET', 'QUIT']:
                contrats = self.userDAO.get_all_contract()
                supports = self.userDAO.get_user_by_role(4)
                choix = self.contractview.logcontracts(self.user, contrats,
                                                       self.userDAO)
                self.handle_main_choice(choix, contrats, supports)

    def handle_main_choice(self, choix, contrats, supports):
        """
        Gère la partie le choix de l'utilisateur pour 
        proposer la bonne redirection
        """
        match choix:
            case _ if choix.startswith("CR"):
                self.create_contract(choix)

            case _ if choix.startswith("A"):
                self.view_contract(choix, contrats, supports)

            case _ if choix.startswith("E"):
                self.view_company(choix)

            case _ if choix.startswith("S"):
                self.delete_contract(choix, contrats)

            case "QUIT":
                quit()

    def create_contract(self, choix):
        """
        Récupère les données de la view pour la création d'un contrat
        Puis fait appel a la fonction add dédiée du DAO
        """
        id = choix[2:]
        company = self.userDAO.get_company(id)
        total_amont, current_amont, sign = self.contractview.createcontract(
            self.user,
            company)
        sign_flag = 1 if sign else 0
        self.userDAO.add_contract(company.id, self.user.id, total_amont,
                                  current_amont, sign_flag)
        if sign_flag == 1: 
            with sentry_sdk.configure_scope() as scope:
                scope.set_tag("action", "creation")
                scope.set_tag("action", "signature")
                scope.set_tag("company :", company.id)
                scope.set_tag("commercial :", self.user.id)
            sentry_sdk.capture_message("Collaborateur a signé un contrat :"
                                       f"Commercial={self.user.nom}, id de "
                                       f"l'entreprise: {company.id}")

    def view_contract(self, choix, contrats, supports):
        id = int(choix[1:])
        contrat = contrats[id]
        contratId = contrat.id
        choix = None
        while choix not in ['RET', 'QUIT']:
            contrat = self.userDAO.get_contract(contratId)
            company = self.userDAO.get_company(contrat.compagny_id)
            events = self.userDAO.get_event_for_contract(contrat.id)
            choix = self.contractview.contractview(self.user, company,
                                                   contrat, events,
                                                   self.userDAO)
            self.contract_choice(choix, contrat, company, events, supports)

    def contract_choice(self, choix, contrat, company, events, supports):
        """
        Gère la partie le choix de l'utilisateur pour 
        proposer la bonne redirection
        """
        match choix:
            case _ if choix.startswith("A"):
                self.view_event(choix)

            case "CR":
                self.create_event(company, contrat, supports)

            case "SUPPRIMER":
                self.delete_contract_if_authorized(contrat, company)
                return 'LIST'

            case _ if choix.startswith("MT "):
                self.update_contract_total(choix, contrat, company)

            case _ if choix.startswith("MV "):
                self.update_contract_current(choix, contrat, company)

            case "MS SI":
                self.update_contract_sign(contrat, company, sign=1)

            case "MS NS":
                self.update_contract_sign(contrat, company, sign=0)

            case "RET":
                return choix

            case "QUIT":
                quit()

    def view_event(self, choix):
        id_event = choix[1:]
        choix = None
        while choix not in ['LIST', 'RET', 'QUIT']:
            event = self.userDAO.get_event(id_event)
            choix = self.eventview.eventview(self.user, event, self.userDAO)
            self.event_choice(choix, event)

    def event_choice(self, choix, event):
        """
        Gère la partie le choix de l'utilisateur pour 
        proposer la bonne redirection
        """
        new_data = choix[3:]
        match choix:
            case "SUPPRIMER":
                self.userDAO.delete_event(event.id)
                return 'LIST'
            case "RET":
                return choix
            case "QUIT":
                quit()
            case _ if choix.startswith("MS"):
                self.userDAO.update_event(
                    event.id, datetime.strptime(new_data,
                                                "%d/%m/%Y %H:%M"),
                    event.event_date_end, event.location,
                    event.id_user, event.attendees, event.notes)
            case _ if choix.startswith("ME"):
                self.userDAO.update_event(
                    event.id, event.event_date_start,
                    datetime.strptime(new_data, "%d/%m/%Y %H:%M"),
                    event.location, event.id_user, event.attendees,
                    event.notes)
            case _ if choix.startswith("ML"):
                self.userDAO.update_event(event.id, event.event_date_start,
                                          event.event_date_end, new_data,
                                          event.id_user, event.attendees,
                                          event.notes)
            case _ if choix.startswith("MA"):
                self.userDAO.update_event(event.id, event.event_date_start,
                                          event.event_date_end, event.location,
                                          event.id_user, new_data, event.notes)
            case _ if choix.startswith("MN"):
                self.userDAO.update_event(event.id, event.event_date_start,
                                          event.event_date_end, event.location,
                                          event.id_user, event.attendees,
                                          new_data)

    def create_event(self, company, contrat, supports):
        """
        Récupère les données de la view pour la création d'un event
        Puis fait appel a la fonction add dédiée du DAO
        """
        if self.user.authorisation('Sale') and self.user.id == company.user_id:
            date_start, date_end, location, support_id, attendees, notes = (
                    self.contractview.createevent(company, self.user, supports)
                )
            eventid = self.userDAO.add_event(date_start, date_end,
                                             location, support_id, attendees,
                                             notes)
            self.userDAO.add_event_contract(eventid, contrat.id)
        else:
            self.view.notautorized(self.user)

    def delete_contract_if_authorized(self, contrat, company):
        if self.user.authorisation('Sale') and self.user.id == company.user_id:
            events = self.userDAO.get_event_for_contract(contrat.id)
            for element in events:
                self.userDAO.delete_event(element.id)
            self.userDAO.delete_contract(contrat.id)
            return 'LIST'
        else:
            self.view.notautorized(self.user)

    def update_contract_total(self, choix, contrat, company):
        if self.user.authorisation('Sale') and self.user.id == company.user_id:
            new_total = float(choix[3:])
            self.userDAO.update_contract(contrat.id, company.id, self.user.id,
                                         new_total, contrat.current_amont,
                                         contrat.sign)
        else:
            self.view.notautorized(self.user)

    def update_contract_current(self, choix, contrat, company):
        if self.user.authorisation('Sale') and self.user.id == company.user_id:
            new_current = float(choix[3:])
            self.userDAO.update_contract(contrat.id, company.id, self.user.id,
                                         contrat.total_amont, new_current,
                                         contrat.sign)
        else:
            self.view.notautorized(self.user)

    def update_contract_sign(self, contrat, company, sign):
        if self.user.authorisation('Sale') and self.user.id == company.user_id:
            self.userDAO.update_contract(contrat.id, company.id, self.user.id,
                                         contrat.total_amont,
                                         contrat.current_amont, sign)
            with sentry_sdk.configure_scope() as scope:
                scope.set_tag("action", "update")
                scope.set_tag("company :", company.id)
                scope.set_tag("action", "signature")
                scope.set_tag("commercial :", self.user.id)
            sentry_sdk.capture_message("Collaborateur à signé un contrat "
                                       f": Commercial={self.user.nom}, id "
                                       f"de l'entreprise: {company.id}")
        else:
            self.view.notautorized(self.user)

    def view_company(self, choix):
        id = choix[1:]
        choix = None
        while choix not in ['LIST', 'RET', 'QUIT']:
            company = self.userDAO.get_company(id)
            contacts = self.userDAO.get_all_contact_by_company_id(id)
            choix = self.clientview.LiteViewCompagny(self.user,
                                                     company, contacts)

    def delete_contract(self, choix, contrats):
        id = int(choix[1:])
        contrat = contrats[id]
        events = self.userDAO.get_event_for_contract(contrat.id)
        for element in events:
            self.userDAO.delete_event(element.id)
        self.userDAO.delete_contract(contrat.id)

    def boucleEvents(self):
        """
        Boucle secondaire
        Elle permet la gestion des events.
        
        """
        if (
            self.user.authorisation('Admin') or
            self.user.authorisation('Gestion') or
            self.user.authorisation('Sale') or
            self.user.authorisation('Support')
        ):
            choix = None
            while choix not in ['RET', 'QUIT']:
                events = self.userDAO.get_all_event_details_with_company()
                choix = self.display_events_based_on_role(events)
                self.handle_events_choice(choix, events)

    def display_events_based_on_role(self, events):
        if self.user.authorisation('Support'):
            return self.eventview.myMensualEvents(self.user, events)
        else:
            return self.eventview.TotalEvents(self.user, events)

    def handle_events_choice(self, choix, events):
        """
        Gère la partie le choix de l'utilisateur pour 
        proposer la bonne redirection
        """
        match choix:
            case "TO":
                self.handle_total_events_choice(events)
            case "TT":
                self.handle_total_events_choice(events)
            case _ if choix.startswith("A"):
                self.boucleSoloEvents(choix)
            case _:
                return choix

    def handle_total_events_choice(self, events):
        choix = None
        while choix not in ['RET', 'QUIT']:
            choix = self.eventview.myTotalEvents(self.user, events)
            if choix.startswith("A"):
                self.boucleSoloEvents(choix)
            elif choix == "TT":
                self.handle_tt_events_choice(events)
            else:
                return choix

    def handle_tt_events_choice(self, events):
        """
        Gère la partie le choix de l'utilisateur pour 
        proposer la bonne redirection
        """
        choix = None
        while choix not in ['RET', 'QUIT']:
            choix = self.eventview.TotalEvents(self.user, events)
            if choix.startswith("A"):
                self.boucleSoloEvents(choix)
            else:
                return choix

    def boucleSoloEvents(self, choix):
        """
        Boucle secondaire
        Elle permet la gestion des events.
        
        """
        id_event = choix[1:]
        choix = None
        while choix not in ['LIST', 'RET', 'QUIT']:
            event = self.userDAO.get_event(id_event)
            choix = self.eventview.eventview(self.user, event, self.userDAO)
            new_data = choix[3:]
            match choix:
                case "SUPPRIMER":
                    self.userDAO.delete_event(event.id)
                    return 'LIST'
                case "RET":
                    return choix
                case "QUIT":
                    quit()
                case _ if choix.startswith("MS "):
                    self.userDAO.update_event(event.id, datetime.strptime(
                        new_data, "%d/%m/%Y %H:%M"), event.event_date_end,
                        event.location, event.id_user, event.attendees,
                        event.notes)
                case _ if choix.startswith("ME "):
                    self.userDAO.update_event(
                        event.id, event.event_date_start,
                        datetime.strptime(new_data, "%d/%m/%Y %H:%M"),
                        event.location, event.id_user, event.attendees,
                        event.notes)
                case _ if choix.startswith("ML "):
                    self.userDAO.update_event(event.id, event.event_date_start,
                                              event.event_date_end, new_data,
                                              event.id_user, event.attendees,
                                              event.notes)
                case _ if choix.startswith("MA "):
                    self.userDAO.update_event(event.id, event.event_date_start,
                                              event.event_date_end,
                                              event.location, event.id_user,
                                              new_data, event.notes)
                case _ if choix.startswith("MN "):
                    self.userDAO.update_event(event.id, event.event_date_start,
                                              event.event_date_end,
                                              event.location, event.id_user,
                                              event.attendees, new_data)
                case _:
                    return choix
