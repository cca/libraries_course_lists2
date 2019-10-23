import config
from .utilities import request_wrapper

# five-letter academic unit name => EQUELLA group name, ldap group name
# good way to get a listing of all the unit codes:
# jq '.[]."academic_units"[0].refid' data/data.json | sed -e 's|AU_||' | sort | uniq
map = {
    "ANIMA": {"group": "Animation Faculty", "ldap": "fac_an"},
    "BARCH": {"group": "Architecture Division Faculty", "ldap": "fac_ar"},
    "CCA": {"group": None, "ldap": None},
    "CERAM": {"group": "Ceramics Faculty", "ldap": "fac_cer"},
    "COMAR": {"group": "Community Arts Faculty", "ldap": "fac_ca"},
    "COMIC": {"group": "Comics MFA Faculty", "ldap": "fac_cm"},
    "CORES": {"group": "First Year Faculty", "ldap": "fac_co"},
    "CRAFT": {"group": "Craft Faculty", "ldap": "fac_craft"},
    "CRTSD": {"group": "Critical Studies Faculty", "ldap": "fac_cr"},
    "CURPR": {"group": "Curatorial Practice Faculty", "ldap": "fac_cu"},
    "DESGN": {"group": "Design MFA Faculty", "ldap": "fac_de"},
    "DIVST": {"group": "Diversity Studies Faculty", "ldap": "fac_di"},
    "DSMBA": {"group": "Design MBA Faculty", "ldap": "fac_de"},
    "EXTED": {"group": None, "ldap": None},
    "FA": {"group": None, "ldap": None},
    "FASHN": {"group": "Fashion Design Faculty", "ldap": "fac_fa"},
    "FILMG": {"group": "Film MFA Faculty", "ldap": "fac_gradfm"},
    "FILMU": {"group": "Film Faculty", "ldap": "fac_fm"},
    "FINAR": {"group": "Graduate Fine Arts Faculty", "ldap": "fac_fina"},
    "FURNT": {"group": "Furniture Faculty", "ldap": "fac_fn"},
    "GLASS": {"group": "Glass Faculty", "ldap": "fac_gl"},
    "GRAPH": {"group": "Graphic Design Faculty", "ldap": "fac_gr"},
    "ILLUS": {"group": "Illustration Faculty", "ldap": "fac_il"},
    "INDIV": {"group": "Individualized Faculty", "ldap": "fac_ind"},
    "INDUS": {"group": "Industrial Design Faculty", "ldap": "fac_in"},
    "INTER": {"group": "Architecture Division Faculty", "ldap": "fac_ar"},
    "IXDGR": {"group": "Interaction Design (MDes) Faculty", "ldap": "fac_ixd"},
    "IXDSN": {"group": "Interaction Design Faculty", "ldap": "fac_ixd"},
    "MAAD": {"group": "Architecture Division Faculty", "ldap": "fac_ar"},
    "MARCH": {"group": "Architecture Division Faculty", "ldap": "fac_ar"},
    "METAL": {"group": "Jewelry Metal Arts Faculty", "ldap": "fac_jma"},
    "PHOTO": {"group": "Photography Faculty", "ldap": "fac_ph"},
    "PNTDR": {"group": "Painting/Drawing Faculty", "ldap": "fac_padr"},
    "PRINT": {"group": "Printmedia Faculty", "ldap": "fac_pm"},
    "SCULP": {"group": "Sculpture Faculty", "ldap": "fac_sc"},
    "TEXTL": {"group": "Textiles Faculty", "ldap": "fac_te"},
    "UDIST": {"group": "Interdisciplinary Faculty", "ldap": "fac_ids"},
    "VISCR": {"group": "Visual Critical Studies Faculty", "ldap": "fac_vcs"},
    "VISST": {"group": "Visual Studies Faculty", "ldap": "fac_vi"},
    "WRITE": {"group": "Writing and Literature Faculty", "ldap": "fac_wl"},
    "WRLIT": {"group": "Writing MFA Faculty", "ldap": "fac_wr"},
}


class Group:
    def __init__(self, group):
        # infuriating inconsistency, group's UUID is named "ID" for some reason
        self.uuid = group["id"]
        self.parentUuid = group.get("parentId", None)
        self.name = group["name"]
        self.users = self.get_users()


    def __repr__(self):
        return self.name


    @property
    def au(self):
        au = [key for key, value in map.items() if value["group"] == self.name][0]
        return au

    # just an alias for the above
    @property
    def academic_unit(self):
        return self.au


    @property
    def ldap(self):
        ldap = [key for key, value in map.items() if value["ldap"] == self.name][0]
        return ldap

    # just an alias for the above
    @property
    def ldap_name(self):
        return self.ldap


    def add_users(self, new_users):
        """
            add list of users to Group

            args: users is a list of usernames (strings)
            returns: group (self)
            throws: HTTP errors from requests
        """
        # deduplicate by casting to a set then back to a list
        all_users = list(set(self.users + users))
        data = {
            "id": self.uuid,
            "name": self.name,
            "users": all_users,
        }

        s = request_wrapper()
        r = s.post(config.api_root + '/usermanagement/local/group/{}'.format(self.uuid), data=data)
        r.raise_for_status()

        print('added {} to {} group'.format(', '.join(new_users), self))
        self.users = all_users
        return self


    def get_users(self):
        """ retrieve list of users in group from EQUELLA
        note that this method is called during the __init__ method
        and populates the self.users list """
        s = request_wrapper()
        r = s.get(config.api_root + '/usermanagement/local/group/{}/user'.format(self.uuid))
        r.raise_for_status()
        """
        results is actually a list of hashes like
        {
          "id": "ephetteplace",
          "links": {
            "self": "https://vault.cca.edu/api/usermanagement/local/user/4bba0672-071e-4dbe-9acd-655a1ed0ef91"
          }
        },
        where the "self" URL for LDAP users is fake and does nothing (can't make this up)
        while all other /local/group/ API routes only care about a list of usernames or
        UUIDs (for internal users)
        """
        users = [p["id"] for p in r.json()["results"]]
        return users


    def write_ldap_file(self):
        with open('data/{}.txt'.format(self.ldap), 'a') as file:
            file.write('\n'.join(self.users))
