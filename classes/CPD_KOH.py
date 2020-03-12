from classes.Distributor_CPD import CPD
from classes.Distributor_OW import OW
from classes.API_PartSmart import API as PartSmart


class KOH(CPD):

    def __init__(self):
        super(KOH, self).__init__('KOH', 'Kohler')

    def get_where_used_kohlerplus(self):

        part_smart = PartSmart('kohler', 'koh', 'kw1116925', '3622Elmst', '9', '9')
        part_smart.get_session()
        product_dicts, product_id_key, filepath = self.open_selected_csv_with_primary_key()
        for product_dict in product_dicts:
            where_used = part_smart.get_part_where_used(product_dict[product_id_key])
            product_dict['WhereUsed'] = [used.split(' ')[0] for used in where_used]
        self.write_list_of_dicts_to_csv(product_dicts, filepath.split('.')[0] + 'where_used.csv')
