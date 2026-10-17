from service import Platform


def build_sample_platform():
    platform = Platform()
    mumbai = platform.add_city("Mumbai", "Maharashtra")
    college = platform.add_college("NMIMS MPSTME", "nmims.edu.in", mumbai.city_id)
    platform.add_recommendation("Shree PG for Students", "pg_hostel", mumbai.city_id, 19.1044, 72.8365, 2,
                                "Shared rooms with meals near campus")
    platform.add_recommendation("Campus Canteen", "restaurant", mumbai.city_id, 19.1050, 72.8370, 1,
                                "Budget thali and snacks")
    platform.add_recommendation("Vile Parle Stationers", "stationery", mumbai.city_id, 19.1030, 72.8380, 1,
                                "Notebooks, drafting supplies, printouts")
    platform.add_recommendation("Juhu Sports Club", "sports", mumbai.city_id, 19.1075, 72.8263, 2,
                                "Badminton and swimming")
    platform.create_admin("Platform Admin", "admin@platform.in", "admin-pass")
    return platform, college
