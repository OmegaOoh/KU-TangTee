<template>
    <div class="drawer h-screen">
        <input id="my-drawer" type="checkbox" class="drawer-toggle" />
        <div class="drawer-content flex flex-col">
            <div
                class="flex items-center p-2 sticky z-50 top-0 left-0 right-0 justify-between bg-base-300 w-screen h-fit border-b-2 border-primary backdrop-blur-md bg-opacity-50"
            >
                <div class="flex justify-start items-center">
                    <label
                        v-if="isAuth"
                        for="my-drawer"
                        @click="() => {getRecentActivity(); getRecentHostActivity()}"
                        class="btn btn-ghost rounded-none drawer-button w-auto h-5"
                    >
                        ☰
                    </label>
                    <p class="flex items-center justify-center mx-2">
                        <RouterLink to="/">KU Tangtee</RouterLink>
                    </p>
                </div>
                <div class="pr-5">
                    <div v-if="!isAuth">
                        <button
                            class="btn btn-ghost rounded-none"
                            @click="login"
                        >
                            Login
                        </button>
                    </div>
                    <div
                        v-else
                        id="profile-dropdown"
                        class="dropdown dropdown-end"
                    >
                        <div tabindex="0" role="button">
                            <img
                                v-if="pfp"
                                v-lazy="pfp"
                                alt="Profile Picture"
                                class="w-8 h-8 rounded-full mr-2 transition-all duration-100 hover:border-opacity-10 hover:border-4"
                            />
                        </div>
                        <ul
                            tabindex="0"
                            class="menu dropdown-content bg-base-300 rounded-box z-20 w-52 p-2 shadow"
                        >
                            <li
                                class="p-2 hover:text-primary cursor-pointer"
                                @click="$router.push(`/profile/${userName}`)"
                            >
                                {{ fName }} {{ lName }}
                            </li>
                            <li @click="logout"><a> Logout </a></li>
                        </ul>
                    </div>
                </div>
            </div>
            <slot><!--Slot Outlet--></slot>
        </div>
        <div class="drawer-side">
            <label
                for="my-drawer"
                aria-label="close sidebar"
                class="drawer-overlay"
            ></label>
            <ul class="menu bg-base-200 text-base-content w-80 p-4">
                <!-- Sidebar content here -->
                <template v-if="activities.length > 0">
                    <li class="text-primary font-semibold mb-2"> Recently Joined </li>
                    <li
                        v-for="(activity, index) in activities"
                        :key="index"
                        class="w-full overflow-hidden h-fit"
                    >
                        <router-link
                            :to="`/activities/${activity.activity_id}`"
                            class="w-full"
                        >
                            <p class="w-full h-fit text-ellipsis overflow-hidden line-ellipsis">
                                {{ activity.name }}
                            </p>
                        </router-link>
                    </li>
                    <div class="divider w-full"></div>
                </template>
                <template v-if="hosted.length > 0">
                    <li class="text-primary font-semibold mb-2"> Recently Hosted </li>
                    <li
                        v-for="(activity, index) in hosted"
                        :key="index"
                        class="w-full overflow-hidden h-fit"
                    >
                        <router-link
                            :to="`/activities/${activity.activity_id}`"
                            class="w-full"
                        >
                            <p class="w-full h-fit text-ellipsis overflow-hidden line-ellipsis">
                                {{ activity.name }}
                            </p>
                        </router-link>
                    </li>
                    <div class="divider w-full"></div>
                </template>
                <li class="w-full mt-auto">
                    <router-link to="/create">Host New Activity</router-link>
                </li>
            </ul>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import {
    login,
    logout,
    authStatus,
    isAuth,
    pfp,
    fName,
    lName,
    userId,
    userName,
} from '@/functions/Authentications';
import apiClient from '@/api';
import { addAlert } from '@/functions/AlertManager';

const activities = ref([]);
const hosted = ref([]);

const getRecentActivity = async () => {
    try {
        const response = await apiClient.get(
            `/activities/get-recently/${userId.value}/?records=5`
        );
        activities.value = response.data;
    } catch (error) {
            if (error.request) {
                addAlert('error', 'Error Connecting to Server')
            } else {
                addAlert('error', error.message)
            }
        }
};

const getRecentHostActivity = async () => {
    try{
        const response = await apiClient.get(
        `/activities/get-recently/${userId.value}?isHost=True&records=5`
        )
        hosted.value = response.data
    } catch (error) {
        if (error.request) {
            addAlert('error', 'Error Connecting to Server')
        } else {
            addAlert('error', error.message)
        }
    }

}

onMounted(() => {
    authStatus();
});
</script>

<style scoped>
.line-ellipsis {
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 1;
    line-clamp: 1;
    word-wrap: break-word;
    overflow: hidden;
    text-overflow: ellipsis;
}
</style>
