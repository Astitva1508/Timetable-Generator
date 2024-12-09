import json
import random
from costs import check_hard_constraints, subjects_order_cost, empty_space_groups_cost, empty_space_teachers_cost, \
    free_hour
from model import Class, Classroom, Data


def load_data(file_path, teachers_empty_space, groups_empty_space, subjects_order):
    """
    Loads and processes input data, initialises helper structures.
    :param file_path: path to file with input data

    :param teachers_empty_space: dictionary where key = name of the teacher, values = list of rows where it is in

    :param groups_empty_space: dictionary where key = group index, values = list of rows where it is in

    :param subjects_order: dictionary where key = (name of the subject, index of the group), value = [int, int, int]
    where ints represent start times (row in matrix) for types of classes P, V and L respectively. If start time is -1
    it means that that subject does not have that type of class.
    
    :return: Data(groups, teachers, classes, classrooms)
    """
    with open(file_path) as file:
        data = json.load(file)

    # classes: dictionary where key = index of a class, value = class
    classes = {}
    # classrooms: dictionary where key = index, value = classroom name
    classrooms = {}
    # teachers: dictionary where key = teachers' name, value = index
    teachers = {}
    # groups: dictionary where key = name of the group, value = index
    groups = {}
    class_list = []

    # add classrooms
    for type in data['Classrooms']:
        for name in data['Classrooms'][type]:
            new = Classroom(name, type)
            classrooms[len(classrooms)] = new

    for cl in data['Classes']:
        new_group = cl['Groups']
        new_teacher = cl['Teacher']

        # initialise for empty space of teachers
        if new_teacher not in teachers_empty_space:
            teachers_empty_space[new_teacher] = []

        # add groups
        for group in new_group:
            if group not in groups:
                groups[group] = len(groups)
                # initialise for empty space of groups
                groups_empty_space[groups[group]] = []

        # every class is assigned a list of classrooms he can be in as indexes (later columns of matrix)
        classroom = cl['Classroom']
        index_classrooms = []
        # add classrooms
        for index, c in classrooms.items():
            if c.type == classroom:
                index_classrooms.append(index)

        for group in new_group:
            group_idx = groups[group]
            new = Class(group_idx,new_teacher,cl['Subject'],cl['Type'],cl['Duration'],index_classrooms)
            class_list.append(new)


        # add teacher
        if new_teacher not in teachers:
            teachers[new_teacher] = len(teachers)

    # shuffle mostly because of teachers
    random.shuffle(class_list)
    
    for cl in class_list:
        classes[len(classes)] = cl

    # every class has a list of groups marked by its index, same for classrooms
    for i in classes:
        cl = classes[i]

        if (cl.subject, cl.groups) not in subjects_order:
            # index for L, V, P
            subjects_order[(cl.subject, cl.groups)] = [-1, -1, -1]
    return Data(groups, teachers, classes, classrooms)


def set_up(num_of_columns):
    """
    Sets up the timetable matrix and dictionary that stores free fields from matrix.
    :param num_of_columns: number of classrooms
    :return: matrix, free
    """
    work_hours = 8
    work_days = 5
    w, h = num_of_columns, work_hours*work_days                                         
    # 5 (workdays) * 12 (work hours) = 60
    matrix = [[None for x in range(w)] for y in range(h)]
    free = []

    # initialise free dict as all the fields from matrix
    # free contains (timeslot,classroom)

    # Representation of time : [0,39]
    for i in range(len(matrix)):
        for j in range(len(matrix[i])):
            free.append((i, j))
    # (x,y) -> xth time par yth room
    
    return matrix, free


def show_timetable(matrix):
    """
    Prints timetable matrix.
    """
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    hours = [9, 10, 11, 12, 13, 14, 15, 16]

    # print heading for classrooms
    for i in range(len(matrix[0])):
        if i == 0:
            print('{:17s} C{:6s}'.format('', '0'), end='')
        else:
            print('C{:6s}'.format(str(i)), end='')
    print()

    d_cnt = 0
    h_cnt = 0
    for i in range(len(matrix)):
        day = days[d_cnt]
        hour = hours[h_cnt]
        print('{:10s} {:2d} ->  '.format(day, hour), end='')
        for j in range(len(matrix[i])):
            print('{:6s} '.format(str(matrix[i][j])), end='')
        print()
        h_cnt += 1
        if h_cnt == 8:
            h_cnt = 0
            d_cnt += 1
            print()


def write_solution_to_file(matrix, data, filled, filepath, groups_empty_space, teachers_empty_space, subjects_order):
    """
    Writes statistics and schedule to file.
    """
    f = open('solution_files/sol_' + filepath, 'w')

    f.write('-------------------------- STATISTICS --------------------------\n')
    cost_hard = check_hard_constraints(matrix, data)
    if cost_hard == 0:
        f.write('\nHard constraints satisfied: 100.00 %\n')
    else:
        f.write('Hard constraints NOT satisfied, cost: {}\n'.format(cost_hard))
    f.write('Soft constraints satisfied: {:.02f} %\n\n'.format(subjects_order_cost(subjects_order)))

    empty_groups, max_empty_group, average_empty_groups = empty_space_groups_cost(groups_empty_space)
    f.write('TOTAL empty space for all GROUPS and all days: {}\n'.format(empty_groups))
    f.write('MAX empty space for GROUP in day: {}\n'.format(max_empty_group))
    f.write('AVERAGE empty space for GROUPS per week: {:.02f}\n\n'.format(average_empty_groups))

    empty_teachers, max_empty_teacher, average_empty_teachers = empty_space_teachers_cost(teachers_empty_space)
    f.write('TOTAL empty space for all TEACHERS and all days: {}\n'.format(empty_teachers))
    f.write('MAX empty space for TEACHER in day: {}\n'.format(max_empty_teacher))
    f.write('AVERAGE empty space for TEACHERS per week: {:.02f}\n\n'.format(average_empty_teachers))

    f_hour = free_hour(matrix)
    if f_hour != -1:
        f.write('Free term -> {}\n'.format(f_hour))
    else:
        f.write('NO hours without classes.\n')

    groups_dict = {}
    for group_name, group_index in data.groups.items():
        if group_index not in groups_dict:
            groups_dict[group_index] = group_name
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    hours = [9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]

    f.write('\n--------------------------- SCHEDULE ---------------------------')
    for class_index, times in filled.items():
        c = data.classes[class_index]
        groups = groups_dict[c.groups] + ', '
        f.write('\n\nClass {}\n'.format(class_index))
        f.write('Teacher: {} \nSubject: {} \nGroups:{} \nType: {} \nDuration: {} hour(s)'
                .format(c.teacher, c.subject, groups[:len(groups) - 2], c.type, c.duration))
        room = str(data.classrooms[times[0][1]])
        f.write('\nClassroom: {:2s}\nTime: {}'.format(room[:room.rfind('-')], days[times[0][0] // 12]))
        for time in times:
            f.write(' {}'.format(hours[time[0] % 12]))
    f.close()


def show_statistics(matrix, data, subjects_order, groups_empty_space, teachers_empty_space):
    """
    Prints statistics.
    """
    cost_hard = check_hard_constraints(matrix, data)
    if cost_hard == 0:
        print('Hard constraints satisfied: 100.00 %')
    else:
        print('Hard constraints NOT satisfied, cost: {}'.format(cost_hard))
    print('Soft constraints satisfied: {:.02f} %\n'.format(subjects_order_cost(subjects_order)))

    empty_groups, max_empty_group, average_empty_groups = empty_space_groups_cost(groups_empty_space)
    print('TOTAL empty space for all GROUPS and all days: ', empty_groups)
    print('MAX empty space for GROUP in day: ', max_empty_group)
    print('AVERAGE empty space for GROUPS per week: {:.02f}\n'.format(average_empty_groups))

    empty_teachers, max_empty_teacher, average_empty_teachers = empty_space_teachers_cost(teachers_empty_space)
    print('TOTAL empty space for all TEACHERS and all days: ', empty_teachers)
    print('MAX empty space for TEACHER in day: ', max_empty_teacher)
    print('AVERAGE empty space for TEACHERS per week: {:.02f}\n'.format(average_empty_teachers))

    f_hour = free_hour(matrix)
    if f_hour != -1:
        print('Free term ->', f_hour)
    else:
        print('NO hours without classes.')

def get_teacher_timetable(matrix, data,teacher_name):
    n = len(matrix)
    m = len(matrix[0])
    teacher_matrix = [[None for x in range(8)] for y in range(5)]
    for i in range(n):
        for j in range(m):
            if matrix[i][j]==None:
                continue
            class_idx = matrix[i][j]
            if data.classes[class_idx].teacher!=teacher_name:
                continue
            teacher_matrix[i//8][i%8] = class_idx
    show_filer_timetable(teacher_matrix)

def get_group_timetable(matrix, data, group_name):
    n = len(matrix)
    m = len(matrix[0])
    group_idx = data.groups[group_name]
    group_matrix = [[None for x in range(8)] for y in range(5)]
    for i in range(n):
        for j in range(m):
            if matrix[i][j]==None:
                continue
            class_idx = matrix[i][j]
            if data.classes[class_idx].groups!=group_idx:
                continue
            group_matrix[i//8][i%8] = class_idx
    show_filer_timetable(group_matrix)

def get_room_timetable(matrix, data, room_idx):
    n = len(matrix)
    m = len(matrix[0])
    room_matrix = [[None for x in range(8)] for y in range(5)]
    for i in range(n):
            if matrix[i][int(room_idx)]==None:
                continue
            class_idx = matrix[i][int(room_idx)]
            room_matrix[i//8][i%8] = class_idx
    show_filer_timetable(room_matrix)

def show_filer_timetable(matrix):
    """
    Prints timetable matrix.
    """
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    hours = [9, 10, 11, 12, 13, 14, 15, 16]

    # print heading for times
    for i in range(len(matrix[0])):
        if i == 0:
            print('{:13s} {:9s}'.format('', str(hours[i])), end='')
        else:
            print('{:9s}'.format(str(hours[i])), end='')
    print()

    for i in range(len(matrix)):
        day = days[i]
        print('{:10s} -> '.format(day), end='')
        for j in range(len(matrix[i])):
            print('{:8s} '.format(str(matrix[i][j])), end='')
        print()

def generate_timetable(matrix, data,teacher=None, group=None, room=None):
    print("\n--- Generated Timetable ---")
    if teacher:
        get_teacher_timetable(matrix,data,teacher)
        print(f"Timetable for Teacher: {teacher}")
    elif group:
        get_group_timetable(matrix,data,group)
        print(f"Timetable for Group: {group}")
    elif room:
        get_room_timetable(matrix, data, room)
        print(f"Timetable for Room: {room}")
    else:
        print("No data provided.")
    print("--------------------------\n")