<template>
    <div class="h-[100vh] w-full overflow-x-hidden">
        <div
            class="breadcrumbs text-lm size-fit my-6 mx-10 w-full h-fit overflow-visible"
        >
            <ul>
                <li><a @click="$router.push('/')">Home</a></li>
                <li>Profile</li>
            </ul>
        </div>
        <div
            class="card p-2 bg-base-300 border-2 border-primary shadow-md rounded-lg m-6"
        >
            <div class="card-body">
                <div class="card p-4 bg-base-100 shadow-md rounded-lg w-full">
                    <div class="card-body flex flex-row justify-start w-full">
                        <button
                            v-if="isOwner"
                            class="absolute cursor-pointer hover:text-primary transition-colors ease-in-out duration-100 left-3 top-2"
                            @click="editMode = true"
                        >
                            ✎
                        </button>
                        <div>
                            <div class="avatar indicator">
                                <span
                                    class="indicator-item indicator-bottom indicator-center badge badge-accent font-semibold"
                                >
                                    KU &nbsp;
                                    <span v-if="!editMode">{{ kuGen }}</span>
                                    <input
                                        v-else
                                        v-model="kuGen"
                                        type="number"
                                        class="w-6 no-arrows px-1 bg-inherit underline"
                                        min="1"
                                        :max="getMaxKuGeneration()"
                                    />
                                </span>

                                <div class="w-24 rounded-md">
                                    <img v-lazy="pfp" />
                                </div>
                            </div>
                            <div class="my-2">
                                <p class="font-semibold text-sm">
                                    Level: {{ reputationLevel }}
                                </p>
                                <progress
                                    class="progress progress-primary w-full bg-base-200"
                                    :value="reputationProgress"
                                    max="10"
                                ></progress>
                                <p class="text-xs text-gray-500 mt-1">
                                    Progress: {{ reputationProgress }} / 10
                                </p>
                                <progress
                                    class="progress progress-warning w-full bg-base-200"
                                    :value="concurrentAct"
                                    :max="joinLimit"
                                ></progress>
                                <p class="text-xs text-gray-500 mt-1">
                                    Ongoing:
                                    {{ concurrentAct }} / {{ joinLimit }}
                                </p>
                            </div>
                        </div>
                        <div class="flex-row ml-3 w-full">
                            <span
                                class="text-2xl font-semibold text-wrap break-words"
                            >
                                {{ user.first_name }} {{ user.last_name }}
                            </span>
                            <span class="text-xs font-light text-primary ml-3">
                                {{ user.username }}
                            </span>
                            <div v-if="!editMode">
                                <span class="text-sm text-secondary">{{
                                    nickname
                                }}</span>
                                <span v-if="nickname && pronoun" class="mx-2">
                                </span>
                                <span class="text-sm text-secondary">
                                    {{ pronoun }}
                                </span>
                            </div>
                            <div v-else class="flex flex-row mt-2 w-[80%]">
                                <input
                                    v-model="nickname"
                                    type="text"
                                    placeholder="Nickname"
                                    maxlength="30"
                                    class="w-[80%] h-fit rounded-md text-primary bg-base-200 border-1 px-2 mr-2 outline-primary focus:outline-double border-primary"
                                />
                                <input
                                    v-model="pronoun"
                                    type="text"
                                    placeholder="Pronoun"
                                    maxlength="20"
                                    class="w-[80%] h-fit rounded-md text-accent bg-base-200 border-1 px-2 outline-accent focus:outline-double"
                                />
                            </div>
                            <div v-if="!editMode">
                                <p class="text-primary break-words text-wrap">
                                    {{ faculty }}
                                </p>
                                <p
                                    class="text-sm font-light text-accent break-words text-wrap"
                                >
                                    {{ major }}
                                </p>
                            </div>
                            <div v-else class="flex flex-col">
                                <input
                                    v-model="faculty"
                                    type="text"
                                    placeholder="Faculty"
                                    maxlength="100"
                                    class="w-[80%] rounded-md text-primary bg-base-200 border-1 my-3 px-2 outline-primary focus:outline-double border-primary"
                                />
                                <input
                                    v-model="major"
                                    type="text"
                                    placeholder="Major"
                                    maxlength="100"
                                    class="w-[80%] rounded-md text-accent bg-base-200 border-1 mb-3 px-2 outline-accent focus:outline-double"
                                />
                            </div>
                            <div v-if="bio || editMode">
                                <p class="pt-2 mb-2 text-sm font-semibold">
                                    Bio
                                </p>
                                <textarea
                                    v-if="!editMode"
                                    v-model="bio"
                                    class="text-xs w-full resize-none bg-inherit break-words"
                                    disabled
                                    rows="2"
                                ></textarea>
                                <textarea
                                    v-else
                                    v-model="bio"
                                    placeholder="Share a little about yourself"
                                    class="text-xs w-full resize-none overflow-hidden break-normal bg-base-200 p-2 rounded-md outline-primary break-words focus:outline-double"
                                    rows="2"
                                    maxlength="256"
                                ></textarea>
                            </div>

                            <div v-if="editMode">
                                <button
                                    class="btn rounded-md absolute top-2 right-2 w-fit h-fit py-1"
                                    :class="isProcessing ? 'btn-disabled' : 'btn-secondary'"
                                    @click="submitData"
                                >
                                    Save
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="flex justify-items-center gap-2">
                    <div class="tabs mt-4 w-full">
                        <a
                            @click="selectedTab = 'joined'"
                            :class="{ 'tab-active': selectedTab === 'joined' }"
                            class="tab tab-bordered w-1/2"
                            >Joined Activities</a
                        >
                        <a
                            @click="selectedTab = 'hosted'"
                            :class="{ 'tab-active': selectedTab === 'hosted' }"
                            class="tab tab-bordered w-1/2"
                            >Hosted Activities</a
                        >
                    </div>
                </div>

                <div v-if="selectedTab === 'joined'" class="pt-4">
                    <div class="flex flex-col">
                        <div
                            class="card bg-base-200 w-full hover:border-primary border-2 border-base-200 transition-all ease-in-out duration-75 mb-4 cursor-pointer"
                            v-for="activity in joinedActivity"
                            :key="activity.activity_id"
                            @click="
                                $router.push(
                                    `/activities/${activity.activity_id}`
                                )
                            "
                        >
                            <div class="card-body">
                                <h2 class="card-title line-clamp-1">
                                    {{ activity.name }}
                                </h2>
                                <p>
                                    <strong>Date and Time: </strong
                                    >{{
                                        formatTimestamp(activity.activity_date)
                                    }}
                                </p>
                            </div>
                        </div>
                    </div>
                </div>

                <div v-if="selectedTab === 'hosted'" class="pt-4">
                    <div class="flex flex-col">
                        <div
                            class="card bg-base-200 w-full hover:border-primary border-2 border-base-200 transition-all ease-in-out duration-75 mb-4 cursor-pointer"
                            v-for="activity in hostedActivity"
                            :key="activity.activity_id"
                            @click="
                                $router.push(
                                    `/activities/${activity.activity_id}`
                                )
                            "
                        >
                            <div class="card-body">
                                <h2 class="card-title line-clamp-1">
                                    {{ activity.name }}
                                </h2>
                                <p>
                                    <strong>Date and Time: </strong
                                    >{{
                                        formatTimestamp(activity.activity_date)
                                    }}
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import apiClient from '@/api';
import { watch, ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { userId } from '@/functions/Authentications';
import { format } from 'date-fns';
import { addAlert } from '@/functions/AlertManager';
import { createPutRequest } from '@/functions/HttpRequest';

const KU_ESTABLISHED_YEAR = 1940;

// Router
const route = useRoute();
const router = useRouter();

// Variable
const user = ref({});
const nickname = ref('');
const pronoun = ref('');
const faculty = ref('');
const major = ref('');
const bio = ref('');
const kuGen = ref('');
const pfp = ref('');
const joinedActivity = ref([]);
const hostedActivity = ref([]);
const selectedTab = ref('joined');
const editMode = ref(false);
const reputation = ref(0);
const reputationLevel = ref(0);
const reputationProgress = ref(0);
const joinLimit = ref(0);
const concurrentAct = ref(0);

const isProcessing = ref(false);

// Computed Properties
const isOwner = computed(() => {
    return user.value.id == userId.value;
});

/**
 * Fetch Data
 */
const fetchUserData = async () => {
    /**
     * Function to fetch data of user from backend.
     * this function return nothing.
     */
    const response = await apiClient.get(
        `/auth/user/${route.params.username}/`
    );
    await apiClient.get(`/profile/check-missing/`);
    user.value = response.data;
    nickname.value = user.value.user_profile.nick_name;
    pronoun.value = user.value.user_profile.pronoun;
    faculty.value = user.value.user_profile.faculty;
    major.value = user.value.user_profile.major;
    kuGen.value = user.value.user_profile.ku_generation;
    bio.value = user.value.user_profile.about_me;
    pfp.value = user.value.user_profile.profile_picture_url;
    reputation.value = user.value.user_profile.reputation_score;
    reputationLevel.value = reputationProgress.value = Math.floor(
        reputation.value / 10
    );
    reputationProgress.value =
        reputation.value === 100 ? 10 : reputation.value % 10;
    concurrentAct.value = user.value.user_profile.active_activity_count;
    joinLimit.value = user.value.user_profile.join_limit;
};

const fetchJoinedActivities = async () => {
    /**
     * Fetch data of recently joined activity.
     * this function returns nothing.
     */
    const response = await apiClient.get(
        `/activities/get-recently/${user.value.id}?byDate=True`
    );
    joinedActivity.value = response.data;
};

const fetchHostedActivities = async () => {
    /**
     * Fetch data of recently hosted activity.
     * this function returns nothing.
     */
    const response = await apiClient.get(
        `/activities/get-recently/${user.value.id}?byDate=True&isHost=True`
    );
    hostedActivity.value = response.data;
};

const onUserChange = (newUsername, oldUsername) => {
    if (newUsername != oldUsername) {
        fetchUserData();
        fetchHostedActivities();
        fetchJoinedActivities();
    }
};

/**
 * Formatter
 */

const formatTimestamp = (timestamp) => {
    /*
     * Format the timestamp into (Oct 22, 2024, 9:00 AM).
     *
     * @params {string} not yet formatted timestamp
     * @returns {string} formatted timestamp
     */
    if (timestamp) {
        return format(new Date(timestamp), 'MMM/dd/yyyy, hh:mm a');
    } else {
        return 'No date provided';
    }
};

/**
 * Validator
 */

const validateInput = () => {
    /**
     * Function to validate the input.
     * @return true if all input were valid.
     */
    var validInput = true;

    if (kuGen.value == null || kuGen.value == '') {
        validInput = false;
        addAlert('error', 'KU Generation is required');
    }
    if (kuGen.value != '') {
        if (kuGen.value < 1) {
            addAlert('warning', 'Your KU Generation must be at least 1');
            validInput = false;
        }
        if (kuGen.value > getMaxKuGeneration()) {
            addAlert(
                'warning',
                'Your KU Generation must be less than or equal to ' +
                    getMaxKuGeneration()
            );
            validInput = false;
        }
    }
    if (faculty.value == '') {
        validInput = false;
        addAlert('error', 'Faculty is required');
    }
    return validInput;
};

const getMaxKuGeneration = () => {
    /**
     * Get current max Ku Generation
     * @returns maximum ku generation (current years - established year)
     */
    const currentYear = new Date().getFullYear();
    return currentYear - KU_ESTABLISHED_YEAR;
};

/**
 * Data sender
 */

const submitData = async () => {
    isProcessing.value = true;
    if (!validateInput()) {
        isProcessing.value = false;
        return; // Invalid input return early
    }
    const response = await createPutRequest(`/profile/${user.value.username}/`, {
        nick_name: nickname.value,
        pronoun: pronoun.value,
        ku_generation: kuGen.value,
        faculty: faculty.value,
        major: major.value,
        about_me: bio.value,
    });
    isProcessing.value = false;
    if (!response) return;
    addAlert('success', 'Your Profile has been edited successfully!');
    editMode.value = false;
};

watch(
    () => route.params.username,
    (newUsername, oldUsername) => {
        onUserChange(newUsername, oldUsername);
    }
);

onMounted(async () => {
    try {
        await fetchUserData();
        fetchHostedActivities();
        fetchJoinedActivities();
    } catch (e) {
        router.push('/not-found');
        addAlert('error', 'The profile does not exists.');
    }
});
</script>

<style scoped>
.line-clamp-2 {
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 2;
    line-clamp: 2;
    word-wrap: break-word;
    overflow: hidden;
    text-overflow: ellipsis;
}

.line-clamp-1 {
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 1;
    line-clamp: 1;
    word-wrap: break-word;
    overflow: hidden;
    text-overflow: ellipsis;
}

.no-arrows {
    -moz-appearance: textfield;
    appearance: textfield;
}

.no-arrows::-webkit-inner-spin-button,
.no-arrows::-webkit-outer-spin-button {
    -webkit-appearance: none;
    margin: 0;
}
</style>
